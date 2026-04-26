"""Tests for PyInstaller packaging configuration."""

import pathlib
import unittest


class TestPyInstallerSpec(unittest.TestCase):
    def test_asr_backend_package_is_collected_for_dynamic_imports(self):
        spec = pathlib.Path("vvrite.spec").read_text(encoding="utf-8")

        self.assertIn('collect_submodules("vvrite.asr_backends")', spec)

    def test_ffmpeg_is_not_bundled(self):
        spec = pathlib.Path("vvrite.spec").read_text(encoding="utf-8")

        self.assertNotIn("ffmpeg", spec.lower())

    def test_build_script_has_local_mode_without_notarization(self):
        script = pathlib.Path("scripts/build.sh").read_text(encoding="utf-8")

        self.assertIn("--local", script)
        self.assertIn("BUILD_MODE=\"local\"", script)
        self.assertIn("LOCAL_SIGN_IDENTITY", script)
        self.assertIn("Skipping notarization", script)


if __name__ == "__main__":
    unittest.main()
