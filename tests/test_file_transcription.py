"""Tests for external file transcription helpers."""

import os
import tempfile
import unittest

from vvrite.file_transcription import (
    is_supported_media_file,
    prepare_transcription_input,
)


class TestFileTranscriptionHelpers(unittest.TestCase):
    def test_supported_media_extensions(self):
        self.assertTrue(is_supported_media_file("/tmp/audio.wav"))
        self.assertTrue(is_supported_media_file("/tmp/audio.mp3"))
        self.assertTrue(is_supported_media_file("/tmp/video.mp4"))
        self.assertFalse(is_supported_media_file("/tmp/note.txt"))

    def test_prepare_transcription_input_copies_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "source.wav")
            with open(source, "wb") as f:
                f.write(b"audio")

            prepared = prepare_transcription_input(source)

            self.assertNotEqual(prepared, source)
            self.assertTrue(os.path.exists(source))
            with open(prepared, "rb") as f:
                self.assertEqual(f.read(), b"audio")


if __name__ == "__main__":
    unittest.main()
