"""Tests for ASR language hint resolution."""

import unittest


class _Prefs:
    asr_language = "auto"
    ui_language = None


class TestAsrLanguageResolution(unittest.TestCase):
    def test_auto_keeps_model_language_detection(self):
        from vvrite.asr_language import resolve_asr_language

        self.assertEqual(resolve_asr_language(_Prefs()), "auto")

    def test_auto_does_not_use_ui_language_as_asr_hint(self):
        from vvrite.asr_language import resolve_asr_language

        prefs = _Prefs()
        prefs.ui_language = "ko"

        self.assertEqual(resolve_asr_language(prefs), "auto")

    def test_manual_language_overrides_system_locale(self):
        from vvrite.asr_language import resolve_asr_language

        prefs = _Prefs()
        prefs.asr_language = "ja"

        self.assertEqual(resolve_asr_language(prefs), "ja")


if __name__ == "__main__":
    unittest.main()
