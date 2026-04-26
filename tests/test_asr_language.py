"""Tests for ASR language hint resolution."""

import unittest
from unittest.mock import patch


class _Prefs:
    asr_language = "auto"
    ui_language = None


class TestAsrLanguageResolution(unittest.TestCase):
    @patch("vvrite.asr_language.resolve_system_locale", return_value="ko")
    def test_auto_uses_system_locale_as_language_hint(self, _mock_locale):
        from vvrite.asr_language import resolve_asr_language

        self.assertEqual(resolve_asr_language(_Prefs()), "ko")

    def test_manual_language_overrides_system_locale(self):
        from vvrite.asr_language import resolve_asr_language

        prefs = _Prefs()
        prefs.asr_language = "ja"

        self.assertEqual(resolve_asr_language(prefs), "ja")


if __name__ == "__main__":
    unittest.main()
