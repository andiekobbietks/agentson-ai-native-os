"""Read-only memory-mapped GGUF tensor access for host reference tooling.

The model file is treated as a trusted, immutable host asset while open.
This class does not load or execute a model and does not provide inference.
"""
from __future__ import annotations

import mmap
import os
from typing import Iterator

from .gguf_format import GGUFError, inspect_gguf_stream
from .gguf_tensor import TensorDecodeError, dequantize_tensor as decode_tensor
from .gguf_tensor import iter_dequantized


class GGUFModelError(RuntimeError):
    """Raised when a GGUF model cannot be safely accessed through this reader."""


def _stat_key(st) -> tuple[int, int, int, int, int]:
    return (
        st.st_dev,
        st.st_ino,
        st.st_size,
        st.st_mtime_ns,
        st.st_ctime_ns,
    )


class GGUFModel:
    """Memory-map one GGUF file and expose validated tensor payloads by name."""

    def __init__(self, path: str | os.PathLike[str]):
        self._path = os.fspath(path)
        self._file = None
        self._map = None
        self._info = None
        self._stat = None
        self._tensors: dict[str, dict] = {}

    def open(self) -> "GGUFModel":
        if self._map is not None or self._file is not None:
            raise GGUFModelError("model is already open")

        stream = open(self._path, "rb")
        mapped = None
        try:
            before = os.fstat(stream.fileno())
            info = inspect_gguf_stream(stream)
            after_parse = os.fstat(stream.fileno())
            if _stat_key(before) != _stat_key(after_parse):
                raise GGUFModelError("model file changed while being inspected")
            if info["file_size"] != after_parse.st_size:
                raise GGUFModelError("model file size changed during inspection")

            mapped = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
            after_map = os.fstat(stream.fileno())
            if _stat_key(after_parse) != _stat_key(after_map):
                raise GGUFModelError("model file changed while being mapped")

            tensors = {tensor["name"]: tensor for tensor in info["tensors"]}
            self._file = stream
            self._map = mapped
            self._info = info
            self._stat = _stat_key(after_map)
            self._tensors = tensors
            return self
        except Exception:
            if mapped is not None:
                mapped.close()
            stream.close()
            raise

    def __enter__(self) -> "GGUFModel":
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return self._map is not None and self._file is not None

    def _require_open(self) -> None:
        if not self.is_open:
            raise GGUFModelError("model is not open")

    def _check_unchanged(self) -> None:
        self._require_open()
        current = _stat_key(os.fstat(self._file.fileno()))
        if current != self._stat:
            raise GGUFModelError("model file changed while open")

    @property
    def architecture(self) -> str | None:
        self._check_unchanged()
        return self._info.get("architecture")

    @property
    def tensor_names(self) -> tuple[str, ...]:
        self._check_unchanged()
        return tuple(self._tensors)

    @property
    def file_info(self) -> dict:
        self._check_unchanged()
        return {
            "format": self._info["format"],
            "version": self._info["version"],
            "byte_order": self._info["byte_order"],
            "architecture": self._info["architecture"],
            "alignment": self._info["alignment"],
            "file_size": self._info["file_size"],
            "tensor_data_offset": self._info["tensor_data_offset"],
            "tensor_count": self._info["tensor_count"],
            "metadata_count": self._info["metadata_count"],
        }

    def tensor_info(self, name: str) -> dict:
        self._check_unchanged()
        tensor = self._tensors.get(name)
        if tensor is None:
            raise KeyError(name)
        result = dict(tensor)
        result["dimensions"] = list(tensor["dimensions"])
        return result

    def _tensor_range(self, name: str) -> tuple[int, int, int]:
        self._check_unchanged()
        tensor = self._tensors.get(name)
        if tensor is None:
            raise KeyError(name)
        if tensor["byte_size"] is None:
            raise GGUFModelError(
                f"full tensor extent is not validated for {tensor['type_name']}"
            )
        start = self._info["tensor_data_offset"] + tensor["offset"]
        end = start + tensor["byte_size"]
        if start < self._info["tensor_data_offset"] or end < start or end > self._info["file_size"]:
            raise GGUFModelError("tensor range exceeds validated model bounds")
        return start, end, tensor["type_code"]

    def iter_tensor(self, name: str) -> Iterator[float]:
        """Stream decoded values; exhaust or close the iterator before closing the model."""
        start, end, type_code = self._tensor_range(name)

        def iterator() -> Iterator[float]:
            self._check_unchanged()
            view = memoryview(self._map)[start:end]
            try:
                yield from iter_dequantized(view, type_code)
                self._check_unchanged()
            except TensorDecodeError as exc:
                raise GGUFModelError(str(exc)) from exc
            finally:
                view.release()

        return iterator()

    def dequantize_tensor(
        self,
        name: str,
        *,
        max_elements: int = 1_000_000,
    ) -> list[float]:
        """Materialise one supported tensor under the decoder's element limit."""
        start, end, type_code = self._tensor_range(name)
        view = memoryview(self._map)[start:end]
        try:
            values = decode_tensor(view, type_code, max_elements=max_elements)
        except TensorDecodeError as exc:
            raise GGUFModelError(str(exc)) from exc
        finally:
            view.release()
        self._check_unchanged()
        return values

    def close(self) -> None:
        if self._map is not None:
            try:
                self._map.close()
            except BufferError as exc:
                raise GGUFModelError(
                    "close active tensor iterators before closing the model"
                ) from exc
            self._map = None
        if self._file is not None:
            self._file.close()
            self._file = None
        self._info = None
        self._stat = None
        self._tensors = {}
