"""Tests for PyInstaller packaging configuration."""

import pathlib
import unittest


class TestPyInstallerSpec(unittest.TestCase):
    def test_asr_backend_package_is_collected_for_dynamic_imports(self):
        spec = pathlib.Path("vvrite.spec").read_text(encoding="utf-8")

        self.assertIn('collect_submodules("vvrite.asr_backends")', spec)


if __name__ == "__main__":
    unittest.main()
