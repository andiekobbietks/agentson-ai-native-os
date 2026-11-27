from __future__ import annotations

import struct
import unittest

from tools.gguf_inspect import GGUFError, inspect_gguf_bytes


def _string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack("<Q", len(raw)) + raw


def _metadata(key: str, value_type: int, payload: bytes) -> bytes:
    return _string(key) + struct.pack("<I", value_type) + payload


def _align(value: int, alignment: int = 32) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _build_gguf(
    *,
    version: int = 3,
    metadata: list[bytes] | None = None,
    tensors: list[tuple[str, tuple[int, ...], int, int]] | None = None,
    tensor_data: bytes = struct.pack("<4f", 1.0, 2.0, 3.0, 4.0),
) -> bytes:
    metadata = metadata if metadata is not None else [
        _metadata("general.architecture", 8, _string("llama")),
        _metadata("general.alignment", 4, struct.pack("<I", 32)),
    ]
    tensors = tensors if tensors is not None else [
        ("token_embd.weight", (2, 2), 0, 0),
    ]
    header = b"GGUF" + struct.pack("<IQQ", version, len(tensors), len(metadata))
    metadata_bytes = b"".join(metadata)
    tensor_bytes = b""
    for name, dimensions, tensor_type, offset in tensors:
        tensor_bytes += _string(name)
        tensor_bytes += struct.pack("<I", len(dimensions))
        tensor_bytes += b"".join(struct.pack("<Q", dim) for dim in dimensions)
        tensor_bytes += struct.pack("<IQ", tensor_type, offset)
    prefix = header + metadata_bytes + tensor_bytes
    data_start = _align(len(prefix))
    return prefix + (b"\0" * (data_start - len(prefix))) + tensor_data


class GGUFInspectorTests(unittest.TestCase):
    def test_valid_f32_tensor_and_metadata(self):
        result = inspect_gguf_bytes(_build_gguf())
        self.assertEqual(result["version"], 3)
        self.assertEqual(result["architecture"], "llama")
        self.assertEqual(result["alignment"], 32)
        self.assertEqual(result["tensor_count"], 1)
        self.assertEqual(result["tensors"][0]["name"], "token_embd.weight")
        self.assertEqual(result["tensors"][0]["dimensions"], [2, 2])
        self.assertEqual(result["tensors"][0]["byte_size"], 16)

    def test_valid_q8_0_block_extent(self):
        payload = struct.pack("<e", 0.5) + bytes(32)
        result = inspect_gguf_bytes(_build_gguf(
            tensors=[("blk.0.attn_q.weight", (32,), 8, 0)],
            tensor_data=payload,
        ))
        self.assertEqual(result["tensors"][0]["type_name"], "Q8_0")
        self.assertEqual(result["tensors"][0]["byte_size"], 34)

    def test_unknown_but_known_to_ggml_layout_has_offset_only(self):
        result = inspect_gguf_bytes(_build_gguf(
            tensors=[("blk.0.attn_q.weight", (64,), 10, 0)],
            tensor_data=bytes(32),
        ))
        self.assertIsNone(result["tensors"][0]["byte_size"])
        self.assertIn("offsets only", result["extent_validation"])

    def test_metadata_array_is_skipped_with_bounds(self):
        array = struct.pack("<IQ", 8, 2) + _string("hello") + _string("world")
        metadata = [
            _metadata("general.architecture", 8, _string("llama")),
            _metadata("general.alignment", 4, struct.pack("<I", 32)),
            _metadata("tokenizer.ggml.tokens", 9, array),
        ]
        result = inspect_gguf_bytes(_build_gguf(metadata=metadata))
        self.assertEqual(result["metadata_count"], 3)

    def test_invalid_magic_rejected(self):
        with self.assertRaisesRegex(GGUFError, "magic"):
            inspect_gguf_bytes(b"NOPE" + bytes(32))

    def test_unsupported_version_rejected(self):
        with self.assertRaisesRegex(GGUFError, "version"):
            inspect_gguf_bytes(_build_gguf(version=99))

    def test_big_endian_rejected_explicitly(self):
        data = b"GGUF" + struct.pack(">IQQ", 3, 0, 0)
        with self.assertRaisesRegex(GGUFError, "big-endian"):
            inspect_gguf_bytes(data)

    def test_truncated_header_rejected(self):
        with self.assertRaisesRegex(GGUFError, "truncated"):
            inspect_gguf_bytes(b"GGUF\x03")

    def test_duplicate_metadata_key_rejected(self):
        metadata = [
            _metadata("general.architecture", 8, _string("llama")),
            _metadata("general.architecture", 8, _string("qwen")),
            _metadata("general.alignment", 4, struct.pack("<I", 32)),
        ]
        with self.assertRaisesRegex(GGUFError, "duplicate"):
            inspect_gguf_bytes(_build_gguf(metadata=metadata))

    def test_invalid_boolean_rejected(self):
        metadata = [
            _metadata("general.architecture", 8, _string("llama")),
            _metadata("general.alignment", 4, struct.pack("<I", 32)),
            _metadata("test.enabled", 7, b"\x02"),
        ]
        with self.assertRaisesRegex(GGUFError, "boolean"):
            inspect_gguf_bytes(_build_gguf(metadata=metadata))

    def test_invalid_alignment_rejected(self):
        metadata = [
            _metadata("general.architecture", 8, _string("llama")),
            _metadata("general.alignment", 4, struct.pack("<I", 24)),
        ]
        with self.assertRaisesRegex(GGUFError, "power of two"):
            inspect_gguf_bytes(_build_gguf(metadata=metadata))

    def test_misaligned_tensor_offset_rejected(self):
        with self.assertRaisesRegex(GGUFError, "not aligned"):
            inspect_gguf_bytes(_build_gguf(
                tensors=[("token_embd.weight", (2, 2), 0, 1)],
            ))

    def test_tensor_data_truncation_rejected(self):
        with self.assertRaisesRegex(GGUFError, "exceeds file bounds"):
            inspect_gguf_bytes(_build_gguf(tensor_data=bytes(8)))

    def test_invalid_tensor_dimensions_rejected(self):
        with self.assertRaisesRegex(GGUFError, "dimensions"):
            inspect_gguf_bytes(_build_gguf(
                tensors=[("bad.tensor", (0, 2), 0, 0)],
            ))

    def test_removed_ggml_type_codes_rejected(self):
        for removed_code in (4, 5, 31, 32, 33, 36, 37, 38):
            with self.subTest(removed_code=removed_code):
                with self.assertRaisesRegex(GGUFError, "unknown GGML"):
                    inspect_gguf_bytes(_build_gguf(
                        tensors=[("removed.tensor", (32,), removed_code, 0)],
                    ))

    def test_unknown_ggml_type_rejected(self):
        with self.assertRaisesRegex(GGUFError, "unknown GGML"):
            inspect_gguf_bytes(_build_gguf(
                tensors=[("bad.tensor", (2, 2), 99, 0)],
            ))

    def test_tensor_ranges_may_not_overlap(self):
        data = bytes(32)
        tensors = [
            ("first.tensor", (2, 2), 0, 0),
            ("second.tensor", (2, 2), 0, 0),
        ]
        with self.assertRaisesRegex(GGUFError, "overlap"):
            inspect_gguf_bytes(_build_gguf(tensors=tensors, tensor_data=data))


if __name__ == "__main__":
    unittest.main()
