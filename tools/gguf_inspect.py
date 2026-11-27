#!/usr/bin/env python3
"""Bounds-checked GGUF metadata and tensor-directory inspector.

This tool does not execute models. It validates the GGUF header, metadata,
tensor descriptors, alignment and the byte extents of the tensor types whose
block layouts are explicitly supported below.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import struct
import sys
from typing import BinaryIO

SUPPORTED_VERSIONS = {2, 3}
MAX_TENSORS = 1_000_000
MAX_METADATA = 100_000
MAX_STRING_BYTES = 1_048_576
MAX_ARRAY_ELEMENTS = 2_000_000
MAX_ARRAY_DEPTH = 8
MAX_DIMENSIONS = 4
MAX_TENSOR_ELEMENTS = 1 << 40
MAX_ALIGNMENT = 4096

META_TYPES = {
    0: ("uint8", 1, "B"),
    1: ("int8", 1, "b"),
    2: ("uint16", 2, "H"),
    3: ("int16", 2, "h"),
    4: ("uint32", 4, "I"),
    5: ("int32", 4, "i"),
    6: ("float32", 4, "f"),
    7: ("bool", 1, "?"),
    8: ("string", None, None),
    9: ("array", None, None),
    10: ("uint64", 8, "Q"),
    11: ("int64", 8, "q"),
    12: ("float64", 8, "d"),
}

# Share one pinned type/layout table between the inspector and decoder.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from runtime.gguf_types import (
    GGML_TYPE_LAYOUTS as TENSOR_LAYOUTS,
    KNOWN_GGML_TYPE_CODES,
)

KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")


class GGUFError(ValueError):
    """Raised when a GGUF file is malformed or outside supported limits."""


class Reader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        current = stream.tell()
        stream.seek(0, os.SEEK_END)
        self.size = stream.tell()
        stream.seek(current)

    def tell(self) -> int:
        return self.stream.tell()

    def remaining(self) -> int:
        return self.size - self.tell()

    def read_exact(self, count: int) -> bytes:
        if count < 0 or count > self.remaining():
            raise GGUFError("truncated file or out-of-bounds read")
        data = self.stream.read(count)
        if len(data) != count:
            raise GGUFError("truncated file")
        return data

    def unpack(self, fmt: str):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.read_exact(size))[0]

    def u8(self) -> int:
        return self.unpack("<B")

    def u32(self) -> int:
        return self.unpack("<I")

    def u64(self) -> int:
        return self.unpack("<Q")

    def string(self, maximum: int = MAX_STRING_BYTES) -> str:
        length = self.u64()
        if length > maximum:
            raise GGUFError("string length exceeds configured limit")
        raw = self.read_exact(length)
        try:
            return raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise GGUFError("string is not valid UTF-8") from exc


def _align_up(value: int, alignment: int) -> int:
    if value < 0 or alignment <= 0:
        raise GGUFError("invalid alignment arithmetic")
    return (value + alignment - 1) & ~(alignment - 1)


def _metadata_value(reader: Reader, value_type: int, depth: int = 0):
    if depth > MAX_ARRAY_DEPTH:
        raise GGUFError("metadata array nesting exceeds configured limit")
    spec = META_TYPES.get(value_type)
    if spec is None:
        raise GGUFError(f"unknown metadata value type: {value_type}")
    name, _, fmt = spec
    if value_type == 8:
        return reader.string()
    if value_type == 9:
        element_type = reader.u32()
        if element_type not in META_TYPES:
            raise GGUFError(f"unknown metadata array element type: {element_type}")
        length = reader.u64()
        if length > MAX_ARRAY_ELEMENTS:
            raise GGUFError("metadata array exceeds configured element limit")
        for _ in range(length):
            _metadata_value(reader, element_type, depth + 1)
        return {
            "kind": "array",
            "element_type": META_TYPES[element_type][0],
            "length": length,
        }
    if value_type == 7:
        raw = reader.u8()
        if raw not in (0, 1):
            raise GGUFError("boolean metadata value must be 0 or 1")
        return bool(raw)
    return reader.unpack("<" + fmt)


def _read_metadata(reader: Reader, count: int) -> dict:
    metadata = {}
    for _ in range(count):
        key = reader.string(maximum=65535)
        try:
            key.encode("ascii", errors="strict")
        except UnicodeEncodeError as exc:
            raise GGUFError("metadata keys must be ASCII") from exc
        if not KEY_PATTERN.fullmatch(key):
            raise GGUFError(f"invalid metadata key: {key!r}")
        if key in metadata:
            raise GGUFError(f"duplicate metadata key: {key}")
        value_type = reader.u32()
        metadata[key] = {
            "type": META_TYPES.get(value_type, ("unknown",))[0],
            "value": _metadata_value(reader, value_type),
        }
    return metadata


def _read_tensors(reader: Reader, count: int) -> list[dict]:
    tensors = []
    names = set()
    for _ in range(count):
        name = reader.string(maximum=64)
        if not name or name in names:
            raise GGUFError("tensor names must be non-empty and unique")
        names.add(name)
        dimensions_count = reader.u32()
        if dimensions_count < 1 or dimensions_count > MAX_DIMENSIONS:
            raise GGUFError("tensor dimension count is outside supported limits")
        dimensions = [reader.u64() for _ in range(dimensions_count)]
        elements = 1
        for dimension in dimensions:
            if dimension == 0 or elements > MAX_TENSOR_ELEMENTS // dimension:
                raise GGUFError("tensor dimensions are zero or overflow configured limit")
            elements *= dimension
        tensor_type = reader.u32()
        if tensor_type not in KNOWN_GGML_TYPE_CODES:
            raise GGUFError(f"unknown GGML tensor type code: {tensor_type}")
        offset = reader.u64()
        layout = TENSOR_LAYOUTS.get(tensor_type)
        byte_size = None
        if layout is not None:
            _, block_elements, block_bytes = layout
            if elements % block_elements != 0:
                raise GGUFError(f"tensor {name!r} element count is invalid for its block type")
            byte_size = (elements // block_elements) * block_bytes
        tensors.append({
            "name": name,
            "dimensions": dimensions,
            "elements": elements,
            "type_code": tensor_type,
            "type_name": layout[0] if layout else f"GGML_TYPE_{tensor_type}",
            "offset": offset,
            "byte_size": byte_size,
        })
    return tensors


def _inspect(reader: Reader) -> dict:
    if reader.read_exact(4) != b"GGUF":
        raise GGUFError("invalid GGUF magic")
    version_bytes = reader.read_exact(4)
    version = struct.unpack("<I", version_bytes)[0]
    if version not in SUPPORTED_VERSIONS:
        big_endian_version = struct.unpack(">I", version_bytes)[0]
        if big_endian_version in SUPPORTED_VERSIONS:
            raise GGUFError("big-endian GGUF is not supported by this inspector")
        raise GGUFError(f"unsupported GGUF version: {version}")

    tensor_count = reader.u64()
    metadata_count = reader.u64()
    if tensor_count > MAX_TENSORS:
        raise GGUFError("tensor count exceeds configured limit")
    if metadata_count > MAX_METADATA:
        raise GGUFError("metadata count exceeds configured limit")
    if tensor_count > reader.remaining() // 24 + 1:
        raise GGUFError("tensor count is impossible for remaining file size")
    if metadata_count > reader.remaining() // 16 + 1:
        raise GGUFError("metadata count is impossible for remaining file size")

    metadata = _read_metadata(reader, metadata_count)
    tensors = _read_tensors(reader, tensor_count)

    alignment_entry = metadata.get("general.alignment")
    alignment = 32
    if alignment_entry is not None:
        if alignment_entry["type"] != "uint32":
            raise GGUFError("general.alignment must be a UINT32")
        alignment = alignment_entry["value"]
    if alignment < 1 or alignment > MAX_ALIGNMENT or alignment & (alignment - 1):
        raise GGUFError("general.alignment must be a supported power of two")

    for tensor in tensors:
        if tensor["offset"] % alignment:
            raise GGUFError(f"tensor {tensor['name']!r} offset is not aligned")

    data_start = _align_up(reader.tell(), alignment)
    if data_start > reader.size:
        raise GGUFError("tensor data alignment exceeds file size")
    padding = reader.read_exact(data_start - reader.tell())
    if any(padding):
        raise GGUFError("tensor data alignment padding must be zero")

    data_bytes = reader.size - data_start
    known_ranges = []
    for tensor in tensors:
        offset = tensor["offset"]
        if offset > data_bytes:
            raise GGUFError(f"tensor {tensor['name']!r} offset exceeds tensor data")
        byte_size = tensor["byte_size"]
        if byte_size is not None:
            end = offset + byte_size
            if end < offset or end > data_bytes:
                raise GGUFError(f"tensor {tensor['name']!r} data exceeds file bounds")
            known_ranges.append((offset, end, tensor["name"]))

    known_ranges.sort()
    for previous, current in zip(known_ranges, known_ranges[1:]):
        if current[0] < previous[1]:
            raise GGUFError(
                f"tensor data ranges overlap: {previous[2]!r} and {current[2]!r}"
            )

    architecture = metadata.get("general.architecture", {}).get("value")
    return {
        "format": "GGUF",
        "version": version,
        "byte_order": "little",
        "tensor_count": tensor_count,
        "metadata_count": metadata_count,
        "architecture": architecture,
        "alignment": alignment,
        "file_size": reader.size,
        "tensor_data_offset": data_start,
        "tensor_data_bytes": data_bytes,
        "tensors": tensors,
        "extent_validation": "complete for F32, F16, Q4_0, Q4_1, Q5_0, Q5_1, Q8_0 and Q8_1; offsets only for other known GGML types",
    }


def inspect_gguf_stream(stream: BinaryIO) -> dict:
    """Inspect a seekable binary stream without closing or repositioning it."""
    try:
        original_position = stream.tell()
        stream.seek(0)
    except (AttributeError, OSError) as exc:
        raise GGUFError("GGUF input stream must be seekable") from exc
    try:
        return _inspect(Reader(stream))
    finally:
        stream.seek(original_position)


def inspect_gguf(path: str | os.PathLike[str]) -> dict:
    """Inspect a GGUF file without loading its tensor payloads into memory."""
    try:
        with open(path, "rb") as stream:
            return inspect_gguf_stream(stream)
    except OSError:
        raise


def inspect_gguf_bytes(data: bytes) -> dict:
    """Inspect in-memory bytes; primarily useful for deterministic tests."""
    return _inspect(Reader(io.BytesIO(data)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="path to a GGUF model file")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)
    try:
        result = inspect_gguf(args.model)
    except (OSError, GGUFError) as exc:
        print(f"gguf-inspect: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
