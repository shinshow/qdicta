"""Tests for user-visible error reporting helpers."""

import unittest


class TestErrorReporting(unittest.TestCase):
    def test_exception_details_include_context_type_message_and_traceback(self):
        from vvrite.main import _format_exception_for_display

        def raise_error():
            raise RuntimeError("There is no Stream(gpu, 0) in current thread")

        try:
            raise_error()
        except RuntimeError as exc:
            details = _format_exception_for_display("Transcription failed", exc)

        self.assertIn("Transcription failed", details)
        self.assertIn("RuntimeError", details)
        self.assertIn("There is no Stream(gpu, 0) in current thread", details)
        self.assertIn("Traceback (most recent call last)", details)
        self.assertIn("raise_error", details)

    def test_short_error_message_uses_first_line_and_truncates(self):
        from vvrite.main import _short_error_message

        message = "Transcription failed\n\n" + ("x" * 200)

        short = _short_error_message(message)

        self.assertEqual("Transcription failed", short)

    def test_short_error_message_truncates_long_single_line(self):
        from vvrite.main import _short_error_message

        short = _short_error_message("x" * 200)

        self.assertLessEqual(len(short), 90)
        self.assertTrue(short.endswith("..."))


if __name__ == "__main__":
    unittest.main()
