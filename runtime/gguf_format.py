"""Bounds-checked GGUF v2/v3 parser and tensor-directory metadata API.

This module validates GGUF structure without loading tensor payloads.
"""
from __future__ import annotations

import io
import os
import re
import struct
from typing import BinaryIO

SUPPORTED_VERSIONS = {2, 3}
MAX_TENSORS = 1_000_000
MAX_METADATA = 100_000
MAX_STRING_BYTES = 1_048_576
MAX_ARRAY_ELEMENTS = 2_000_000
MAX_ARRAY_DEPTH = 8
MAX_RETAINED_ARRAY_ELEMENTS = 250_000
MAX_RETAINED_ARRAY_BYTES = 8 * 1024 * 1024
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

from .gguf_types import (
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


def _metadata_value(
    reader: Reader,
    value_type: int,
    depth: int = 0,
    *,
    retain_array: bool = False,
    max_retained_array_elements: int = MAX_RETAINED_ARRAY_ELEMENTS,
    max_retained_array_bytes: int = MAX_RETAINED_ARRAY_BYTES,
):
    if depth > MAX_ARRAY_DEPTH:
        raise GGUFError("metadata array nesting exceeds configured limit")
    spec = META_TYPES.get(value_type)
    if spec is None:
        raise GGUFError(f"unknown metadata value type: {value_type}")
    _, _, fmt = spec
    if value_type == 8:
        return reader.string()
    if value_type == 9:
        element_type = reader.u32()
        if element_type not in META_TYPES:
            raise GGUFError(f"unknown metadata array element type: {element_type}")
        length = reader.u64()
        if length > MAX_ARRAY_ELEMENTS:
            raise GGUFError("metadata array exceeds configured element limit")
        if retain_array:
            if element_type == 9:
                raise GGUFError("nested metadata arrays cannot be retained")
            if length > max_retained_array_elements:
                raise GGUFError("retained metadata array exceeds configured element limit")
            values = []
            array_start = reader.tell()
            for _ in range(length):
                values.append(_metadata_value(reader, element_type, depth + 1))
                if reader.tell() - array_start > max_retained_array_bytes:
                    raise GGUFError("retained metadata array exceeds configured byte limit")
            return {
                "kind": "array",
                "element_type": META_TYPES[element_type][0],
                "length": length,
                "values": values,
            }
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


def _read_metadata(
    reader: Reader,
    count: int,
    retain_metadata_keys: frozenset[str],
    max_retained_array_elements: int,
    max_retained_array_bytes: int,
) -> dict:
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
            "value": _metadata_value(
                reader,
                value_type,
                retain_array=key in retain_metadata_keys,
                max_retained_array_elements=max_retained_array_elements,
                max_retained_array_bytes=max_retained_array_bytes,
            ),
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


def _inspect(
    reader: Reader,
    *,
    retain_metadata_keys: frozenset[str] = frozenset(),
    max_retained_array_elements: int = MAX_RETAINED_ARRAY_ELEMENTS,
    max_retained_array_bytes: int = MAX_RETAINED_ARRAY_BYTES,
) -> dict:
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

    metadata = _read_metadata(
        reader,
        metadata_count,
        retain_metadata_keys,
        max_retained_array_elements,
        max_retained_array_bytes,
    )
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


def _normalise_retained_keys(keys) -> frozenset[str]:
    if keys is None:
        return frozenset()
    try:
        retained = frozenset(keys)
    except TypeError as exc:
        raise GGUFError("retained metadata keys must be an iterable of strings") from exc
    if any(not isinstance(key, str) or not KEY_PATTERN.fullmatch(key) for key in retained):
        raise GGUFError("retained metadata keys must be valid GGUF metadata names")
    return retained


def _validate_retention_limits(max_elements: int, max_bytes: int) -> None:
    if type(max_elements) is not int or max_elements < 0:
        raise GGUFError("retained metadata element limit must be a non-negative integer")
    if type(max_bytes) is not int or max_bytes < 0:
        raise GGUFError("retained metadata byte limit must be a non-negative integer")


def inspect_gguf_stream(
    stream: BinaryIO,
    *,
    retain_metadata_keys=(),
    max_retained_array_elements: int = MAX_RETAINED_ARRAY_ELEMENTS,
    max_retained_array_bytes: int = MAX_RETAINED_ARRAY_BYTES,
) -> dict:
    """Inspect a seekable stream, optionally retaining selected metadata arrays."""
    retained = _normalise_retained_keys(retain_metadata_keys)
    _validate_retention_limits(max_retained_array_elements, max_retained_array_bytes)
    try:
        original_position = stream.tell()
        stream.seek(0)
    except (AttributeError, OSError) as exc:
        raise GGUFError("GGUF input stream must be seekable") from exc
    try:
        return _inspect(
            Reader(stream),
            retain_metadata_keys=retained,
            max_retained_array_elements=max_retained_array_elements,
            max_retained_array_bytes=max_retained_array_bytes,
        )
    finally:
        stream.seek(original_position)


def inspect_gguf(
    path: str | os.PathLike[str],
    *,
    retain_metadata_keys=(),
    max_retained_array_elements: int = MAX_RETAINED_ARRAY_ELEMENTS,
    max_retained_array_bytes: int = MAX_RETAINED_ARRAY_BYTES,
) -> dict:
    """Inspect a GGUF file without loading tensor payloads into memory."""
    with open(path, "rb") as stream:
        return inspect_gguf_stream(
            stream,
            retain_metadata_keys=retain_metadata_keys,
            max_retained_array_elements=max_retained_array_elements,
            max_retained_array_bytes=max_retained_array_bytes,
        )


def inspect_gguf_bytes(
    data: bytes,
    *,
    retain_metadata_keys=(),
    max_retained_array_elements: int = MAX_RETAINED_ARRAY_ELEMENTS,
    max_retained_array_bytes: int = MAX_RETAINED_ARRAY_BYTES,
) -> dict:
    """Inspect in-memory bytes; primarily useful for deterministic tests."""
    retained = _normalise_retained_keys(retain_metadata_keys)
    _validate_retention_limits(max_retained_array_elements, max_retained_array_bytes)
    return _inspect(
        Reader(io.BytesIO(data)),
        retain_metadata_keys=retained,
        max_retained_array_elements=max_retained_array_elements,
        max_retained_array_bytes=max_retained_array_bytes,
    )


