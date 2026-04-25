"""Tests for whisper.cpp backend."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from vvrite.asr_models import OUTPUT_MODE_TRANSCRIBE, OUTPUT_MODE_TRANSLATE_TO_ENGLISH
from vvrite.asr_backends import whisper_cpp


class _Prefs:
    asr_language = "ko"
    output_mode = OUTPUT_MODE_TRANSCRIBE
    custom_words = "MLX, vvrite"


class TestWhisperCppBackend(unittest.TestCase):
    def test_model_cache_path_uses_local_filename(self):
        model = MagicMock(key="whisper_large_v3", local_filename="ggml-large-v3.bin")
        with patch("vvrite.model_store.model_root", return_value="/tmp/models"):
            self.assertEqual(
                whisper_cpp.model_path(model),
                "/tmp/models/whisper_large_v3/ggml-large-v3.bin",
            )

    def test_is_cached_requires_file(self):
        model = MagicMock(key="whisper_large_v3", local_filename="ggml-large-v3.bin")
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vvrite.model_store.model_root", return_value=tmp):
                self.assertFalse(whisper_cpp.is_cached(model))
                os.makedirs(os.path.join(tmp, "whisper_large_v3"), exist_ok=True)
                open(
                    os.path.join(tmp, "whisper_large_v3", "ggml-large-v3.bin"),
                    "wb",
                ).close()
                self.assertTrue(whisper_cpp.is_cached(model))

    @patch("vvrite.asr_backends.whisper_cpp.subprocess.run")
    @patch("vvrite.asr_backends.whisper_cpp.binary_path", return_value="/app/whisper-cli")
    @patch(
        "vvrite.asr_backends.whisper_cpp.model_path",
        return_value="/models/ggml-large-v3.bin",
    )
    @patch("vvrite.audio_utils.normalize", return_value="/tmp/normalized.wav")
    def test_transcribe_invokes_whisper_cpp_with_language(
        self, mock_normalize, mock_model_path, mock_binary_path, mock_run
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout=" 안녕하세요 MLX", stderr="")
        model = MagicMock()
        result = whisper_cpp.transcribe("/tmp/raw.wav", model, _Prefs())
        self.assertEqual(result, "안녕하세요 MLX")
        args = mock_run.call_args.args[0]
        self.assertIn("-l", args)
        self.assertIn("ko", args)
        self.assertNotIn("--translate", args)

    @patch("vvrite.asr_backends.whisper_cpp.subprocess.run")
    @patch("vvrite.asr_backends.whisper_cpp.binary_path", return_value="/app/whisper-cli")
    @patch(
        "vvrite.asr_backends.whisper_cpp.model_path",
        return_value="/models/ggml-large-v3.bin",
    )
    @patch("vvrite.audio_utils.normalize", return_value="/tmp/normalized.wav")
    def test_translate_mode_adds_translate_flag(
        self, mock_normalize, mock_model_path, mock_binary_path, mock_run
    ):
        prefs = _Prefs()
        prefs.output_mode = OUTPUT_MODE_TRANSLATE_TO_ENGLISH
        prefs.asr_language = "auto"
        mock_run.return_value = MagicMock(returncode=0, stdout="Hello", stderr="")
        whisper_cpp.transcribe("/tmp/raw.wav", MagicMock(), prefs)
        self.assertIn("--translate", mock_run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
