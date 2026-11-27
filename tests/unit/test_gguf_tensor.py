import math
import struct
import unittest

from runtime.gguf_tensor import TensorDecodeError, dequantize_tensor, iter_dequantized


class GGUFDequantizationTests(unittest.TestCase):
    def test_f32_and_f16(self):
        self.assertEqual(
            dequantize_tensor(struct.pack("<2f", -1.25, 2.5), 0),
            [-1.25, 2.5],
        )
        self.assertEqual(
            dequantize_tensor(struct.pack("<2e", -0.5, 1.25), 1),
            [-0.5, 1.25],
        )

    def test_q4_0_low_nibbles_precede_high_nibbles(self):
        block = struct.pack("<e", 0.5) + bytes([0x89] * 16)
        values = dequantize_tensor(block, 2)
        self.assertEqual(values[:16], [0.5] * 16)
        self.assertEqual(values[16:], [0.0] * 16)

    def test_q4_1_affine_values(self):
        block = struct.pack("<ee", 0.5, 1.0) + bytes([0x21] * 16)
        values = dequantize_tensor(block, 3)
        self.assertEqual(values[:16], [1.5] * 16)
        self.assertEqual(values[16:], [2.0] * 16)

    def test_q5_0_uses_packed_high_bits_for_both_halves(self):
        high_bits = 0x00010001
        block = struct.pack("<eI", 0.25, high_bits) + bytes(16)
        values = dequantize_tensor(block, 6)
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[1:16], [-4.0] * 15)
        self.assertEqual(values[16], 0.0)
        self.assertEqual(values[17:], [-4.0] * 15)

    def test_q5_1_affine_values_and_high_bits(self):
        high_bits = 0x00010001
        block = struct.pack("<eeI", 0.5, 1.0, high_bits) + bytes(16)
        values = dequantize_tensor(block, 7)
        self.assertEqual(values[0], 9.0)
        self.assertEqual(values[1:16], [1.0] * 15)
        self.assertEqual(values[16], 9.0)
        self.assertEqual(values[17:], [1.0] * 15)

    def test_q8_0_signed_values(self):
        quants = tuple(range(-16, 16))
        block = struct.pack("<e32b", 0.5, *quants)
        values = dequantize_tensor(block, 8)
        self.assertEqual(values, [q * 0.5 for q in quants])

    def test_q8_1_signed_values_and_auxiliary_sum(self):
        quants = tuple(range(-16, 16))
        scale = 0.25
        auxiliary_sum = scale * sum(quants)
        block = struct.pack("<ee32b", scale, auxiliary_sum, *quants)
        values = dequantize_tensor(block, 9)
        self.assertEqual(values, [q * scale for q in quants])

    def test_q8_1_nonfinite_auxiliary_sum_rejected(self):
        block = struct.pack("<ee32b", 0.5, math.nan, *([0] * 32))
        with self.assertRaisesRegex(TensorDecodeError, "auxiliary sum"):
            dequantize_tensor(block, 9)

    def test_nonfinite_float_value_rejected(self):
        with self.assertRaisesRegex(TensorDecodeError, "non-finite"):
            dequantize_tensor(struct.pack("<f", math.nan), 0)

    def test_nonfinite_quantization_scale_rejected(self):
        block = struct.pack("<e", math.inf) + bytes(16)
        with self.assertRaisesRegex(TensorDecodeError, "scale"):
            dequantize_tensor(block, 2)

    def test_nonfinite_affine_minimum_rejected(self):
        block = struct.pack("<ee", 0.5, math.nan) + bytes(16)
        with self.assertRaisesRegex(TensorDecodeError, "minimum"):
            dequantize_tensor(block, 3)

    def test_truncated_quantized_block_rejected(self):
        with self.assertRaisesRegex(TensorDecodeError, "payload is truncated"):
            dequantize_tensor(bytes(17), 2)

    def test_unsupported_quantized_type_rejected(self):
        with self.assertRaisesRegex(TensorDecodeError, "unsupported"):
            dequantize_tensor(bytes(32), 10)

    def test_materialized_element_limit_enforced(self):
        block = struct.pack("<e32b", 1.0, *([0] * 32))
        with self.assertRaisesRegex(TensorDecodeError, "element limit"):
            dequantize_tensor(block, 8, max_elements=31)

    def test_iterator_streams_values(self):
        block = struct.pack("<e32b", 0.5, *([2] * 32))
        self.assertEqual(list(iter_dequantized(block, 8)), [1.0] * 32)

    def test_empty_payload_is_empty_tensor(self):
        self.assertEqual(dequantize_tensor(b"", 0), [])
        self.assertEqual(dequantize_tensor(b"", 8), [])

    def test_type_code_must_be_integer(self):
        with self.assertRaisesRegex(TensorDecodeError, "type code"):
            dequantize_tensor(bytes(2), True)


if __name__ == "__main__":
    unittest.main()
