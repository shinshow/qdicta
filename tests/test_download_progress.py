"""Tests for model download progress formatting."""

import unittest

from vvrite.download_progress import format_bytes, format_progress


class TestDownloadProgressFormatting(unittest.TestCase):
    def test_format_bytes_uses_binary_units(self):
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1536), "1.5 KiB")
        self.assertEqual(format_bytes(2 * 1024 * 1024), "2.0 MiB")
        self.assertEqual(format_bytes(3 * 1024 * 1024 * 1024), "3.0 GiB")

    def test_format_progress_with_total_includes_percent(self):
        self.assertEqual(
            format_progress(512 * 1024 * 1024, 2 * 1024 * 1024 * 1024),
            "512.0 MiB / 2.0 GiB (25%)",
        )

    def test_format_progress_without_total_shows_downloaded_bytes(self):
        self.assertEqual(
            format_progress(512 * 1024 * 1024, 0),
            "512.0 MiB downloaded",
        )


if __name__ == "__main__":
    unittest.main()
