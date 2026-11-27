"""Host-side GGUF tensor dequantization for a deliberately bounded type set.

The routines are independent Python implementations of the pinned GGML block
layouts. They are reference/validation code, not a production inference kernel.
"""
from __future__ import annotations

import math
import struct
from typing import Iterator

from .gguf_types import GGML_TYPE_LAYOUTS


class TensorDecodeError(ValueError):
    """Raised when tensor bytes cannot be safely decoded."""


def _half(view: memoryview, offset: int, field: str) -> float:
    value = struct.unpack_from("<e", view, offset)[0]
    if not math.isfinite(value):
        raise TensorDecodeError(f"{field} must be finite")
    return float(value)


def iter_dequantized(data: bytes | bytearray | memoryview, type_code: int) -> Iterator[float]:
    """Yield tensor values in logical row order without materialising the result."""
    if type(type_code) is not int:
        raise TensorDecodeError("tensor type code must be an integer")
    try:
        view = memoryview(data).cast("B")
    except (TypeError, ValueError, BufferError) as exc:
        raise TensorDecodeError("tensor data must be a contiguous bytes-like buffer") from exc

    layout = GGML_TYPE_LAYOUTS.get(type_code)
    if layout is None:
        raise TensorDecodeError(f"unsupported GGML tensor type for dequantization: {type_code}")

    name, block_elements, block_bytes = layout
    if len(view) % block_bytes:
        raise TensorDecodeError(f"{name} payload length is not a whole number of blocks")

    if type_code in (0, 1):
        fmt = "<f" if type_code == 0 else "<e"
        scalar_bytes = 4 if type_code == 0 else 2
        for offset in range(0, len(view), scalar_bytes):
            value = struct.unpack_from(fmt, view, offset)[0]
            if not math.isfinite(value):
                raise TensorDecodeError(f"{name} tensor contains a non-finite value")
            yield float(value)
        return

    for block_offset in range(0, len(view), block_bytes):
        d = _half(view, block_offset, f"{name} scale")
        if type_code == 2:  # Q4_0
            qs_offset = block_offset + 2
            low, high = [], []
            for j in range(16):
                packed = view[qs_offset + j]
                low.append((packed & 0x0F) - 8)
                high.append((packed >> 4) - 8)
            for quant in low:
                yield quant * d
            for quant in high:
                yield quant * d
        elif type_code == 3:  # Q4_1
            m = _half(view, block_offset + 2, "Q4_1 minimum")
            qs_offset = block_offset + 4
            low, high = [], []
            for j in range(16):
                packed = view[qs_offset + j]
                low.append(packed & 0x0F)
                high.append(packed >> 4)
            for quant in low:
                yield quant * d + m
            for quant in high:
                yield quant * d + m
        elif type_code == 6:  # Q5_0
            high_bits = struct.unpack_from("<I", view, block_offset + 2)[0]
            qs_offset = block_offset + 6
            low, high = [], []
            for j in range(16):
                packed = view[qs_offset + j]
                low_high_bit = ((high_bits >> j) & 1) << 4
                high_high_bit = ((high_bits >> (j + 16)) & 1) << 4
                low.append(((packed & 0x0F) | low_high_bit) - 16)
                high.append(((packed >> 4) | high_high_bit) - 16)
            for quant in low:
                yield quant * d
            for quant in high:
                yield quant * d
        elif type_code == 7:  # Q5_1
            m = _half(view, block_offset + 2, "Q5_1 minimum")
            high_bits = struct.unpack_from("<I", view, block_offset + 4)[0]
            qs_offset = block_offset + 8
            low, high = [], []
            for j in range(16):
                packed = view[qs_offset + j]
                low_high_bit = ((high_bits >> j) & 1) << 4
                high_high_bit = ((high_bits >> (j + 16)) & 1) << 4
                low.append((packed & 0x0F) | low_high_bit)
                high.append((packed >> 4) | high_high_bit)
            for quant in low:
                yield quant * d + m
            for quant in high:
                yield quant * d + m
        elif type_code == 8:  # Q8_0
            qs_offset = block_offset + 2
            quants = struct.unpack_from("<32b", view, qs_offset)
            for quant in quants:
                yield quant * d
        elif type_code == 9:  # Q8_1; s is an auxiliary precomputed sum
            s = _half(view, block_offset + 2, "Q8_1 auxiliary sum")
            del s
            qs_offset = block_offset + 4
            quants = struct.unpack_from("<32b", view, qs_offset)
            for quant in quants:
                yield quant * d


def dequantize_tensor(
    data: bytes | bytearray | memoryview,
    type_code: int,
    *,
    max_elements: int = 1_000_000,
) -> list[float]:
    """Materialise a small tensor after enforcing an explicit element limit."""
    if type(max_elements) is not int or max_elements < 0:
        raise TensorDecodeError("max_elements must be a non-negative integer")
    if type(type_code) is not int:
        raise TensorDecodeError("tensor type code must be an integer")
    layout = GGML_TYPE_LAYOUTS.get(type_code)
    if layout is None:
        raise TensorDecodeError(f"unsupported GGML tensor type for dequantization: {type_code}")
    _, block_elements, block_bytes = layout
    try:
        byte_length = memoryview(data).nbytes
    except TypeError as exc:
        raise TensorDecodeError("tensor data must be bytes-like") from exc
    if byte_length % block_bytes:
        raise TensorDecodeError("tensor payload is truncated")
    element_count = (byte_length // block_bytes) * block_elements
    if element_count > max_elements:
        raise TensorDecodeError("tensor exceeds configured element limit")
    return list(iter_dequantized(data, type_code))
