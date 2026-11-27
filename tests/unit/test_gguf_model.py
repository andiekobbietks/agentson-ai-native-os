import io
import os
import struct
import tempfile
import unittest

from runtime.gguf_format import GGUFError, inspect_gguf_stream
from runtime.gguf_model import GGUFModel, GGUFModelError


def _string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack("<Q", len(raw)) + raw


def _metadata(key: str, value_type: int, payload: bytes) -> bytes:
    return _string(key) + struct.pack("<I", value_type) + payload


def _align(value: int, alignment: int = 32) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _build_gguf(
    *,
    tensor_name="weights",
    dimensions=(2,),
    tensor_type=0,
    tensor_data=struct.pack("<2f", 1.25, -2.5),
) -> bytes:
    metadata = [
        _metadata("general.architecture", 8, _string("tiny")),
        _metadata("general.alignment", 4, struct.pack("<I", 32)),
    ]
    header = b"GGUF" + struct.pack("<IQQ", 3, 1, len(metadata))
    metadata_bytes = b"".join(metadata)
    tensor_info = (
        _string(tensor_name)
        + struct.pack("<I", len(dimensions))
        + b"".join(struct.pack("<Q", dim) for dim in dimensions)
        + struct.pack("<IQ", tensor_type, 0)
    )
    prefix = header + metadata_bytes + tensor_info
    data_start = _align(len(prefix))
    return prefix + bytes(data_start - len(prefix)) + tensor_data


class GGUFModelReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "tiny.gguf")
        with open(self.path, "wb") as stream:
            stream.write(_build_gguf())

    def tearDown(self):
        self.temp.cleanup()

    def test_stream_inspection_preserves_position(self):
        stream = io.BytesIO(_build_gguf())
        stream.seek(7)
        info = inspect_gguf_stream(stream)
        self.assertEqual(stream.tell(), 7)
        self.assertEqual(info["architecture"], "tiny")
        self.assertEqual(info["tensor_count"], 1)

    def test_mmap_reader_loads_and_dequantizes_tensor(self):
        with GGUFModel(self.path) as model:
            self.assertTrue(model.is_open)
            self.assertEqual(model.architecture, "tiny")
            self.assertEqual(model.tensor_names, ("weights",))
            self.assertEqual(model.dequantize_tensor("weights"), [1.25, -2.5])
            self.assertEqual(list(model.iter_tensor("weights")), [1.25, -2.5])
            info = model.tensor_info("weights")
            self.assertEqual(info["dimensions"], [2])
            self.assertEqual(model.file_info["version"], 3)
        self.assertFalse(model.is_open)

    def test_q8_1_tensor_is_read_from_mapped_file(self):
        payload = struct.pack("<ee32b", 0.5, 0.0, *([1] * 32))
        path = os.path.join(self.temp.name, "q8_1.gguf")
        with open(path, "wb") as stream:
            stream.write(_build_gguf(
                tensor_name="q8.weight",
                dimensions=(32,),
                tensor_type=9,
                tensor_data=payload,
            ))
        with GGUFModel(path) as model:
            values = model.dequantize_tensor("q8.weight")
            self.assertEqual(values, [0.5] * 32)

    def test_unknown_extent_type_is_not_loaded(self):
        path = os.path.join(self.temp.name, "unknown.gguf")
        with open(path, "wb") as stream:
            stream.write(_build_gguf(
                tensor_name="unknown.weight",
                dimensions=(32,),
                tensor_type=10,
                tensor_data=bytes(32),
            ))
        with GGUFModel(path) as model:
            with self.assertRaisesRegex(GGUFModelError, "extent is not validated"):
                model.dequantize_tensor("unknown.weight")

    def test_missing_tensor_raises_key_error(self):
        with GGUFModel(self.path) as model:
            with self.assertRaises(KeyError):
                model.tensor_info("missing")

    def test_materialization_limit_is_enforced(self):
        with GGUFModel(self.path) as model:
            with self.assertRaisesRegex(GGUFModelError, "element limit"):
                model.dequantize_tensor("weights", max_elements=1)

    def test_active_iterator_must_be_closed_before_model(self):
        model = GGUFModel(self.path).open()
        iterator = model.iter_tensor("weights")
        self.assertEqual(next(iterator), 1.25)
        with self.assertRaisesRegex(GGUFModelError, "active tensor iterators"):
            model.close()
        iterator.close()
        model.close()
        self.assertFalse(model.is_open)

    def test_model_file_modification_is_detected(self):
        model = GGUFModel(self.path).open()
        stat_before = os.stat(self.path)
        os.utime(
            self.path,
            ns=(stat_before.st_atime_ns, stat_before.st_mtime_ns + 1_000_000_000),
        )
        with self.assertRaisesRegex(GGUFModelError, "changed while open"):
            model.tensor_info("weights")
        model.close()

    def test_invalid_gguf_is_rejected_and_file_handle_closed(self):
        bad_path = os.path.join(self.temp.name, "bad.gguf")
        with open(bad_path, "wb") as stream:
            stream.write(b"NOPE")
        model = GGUFModel(bad_path)
        with self.assertRaises(GGUFError):
            model.open()
        self.assertFalse(model.is_open)

    def test_open_twice_is_rejected(self):
        model = GGUFModel(self.path).open()
        with self.assertRaisesRegex(GGUFModelError, "already open"):
            model.open()
        model.close()

    def test_closed_model_rejects_tensor_access(self):
        model = GGUFModel(self.path).open()
        model.close()
        with self.assertRaisesRegex(GGUFModelError, "not open"):
            model.tensor_names


if __name__ == "__main__":
    unittest.main()
