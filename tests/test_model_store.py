"""Tests for app-managed model storage."""

import os
import tempfile
import unittest
from unittest.mock import patch

from vvrite import model_store


class TestModelStore(unittest.TestCase):
    def test_model_root_is_under_application_support(self):
        with patch.object(
            model_store,
            "_application_support_dir",
            return_value="/Users/test/Library/Application Support/vvrite",
        ):
            self.assertEqual(
                model_store.model_root(),
                "/Users/test/Library/Application Support/vvrite/models",
            )

    def test_model_dir_uses_model_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(model_store, "model_root", return_value=tmp):
                path = model_store.model_dir("whisper_large_v3")
                self.assertEqual(path, os.path.join(tmp, "whisper_large_v3"))
                self.assertTrue(os.path.isdir(path))

    def test_model_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(model_store, "model_root", return_value=tmp):
                self.assertEqual(
                    model_store.model_file_path(
                        "whisper_large_v3", "ggml-large-v3.bin"
                    ),
                    os.path.join(tmp, "whisper_large_v3", "ggml-large-v3.bin"),
                )

    def test_delete_model_dir_removes_only_requested_model_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(model_store, "model_root", return_value=tmp):
                target = model_store.model_dir("whisper_large_v3")
                keep = model_store.model_dir("qwen3_asr_1_7b_8bit")
                open(os.path.join(target, "model.bin"), "wb").close()
                open(os.path.join(keep, "model.bin"), "wb").close()
                model_store.delete_model_dir("whisper_large_v3")
                self.assertFalse(os.path.exists(target))
                self.assertTrue(os.path.exists(keep))


if __name__ == "__main__":
    unittest.main()
