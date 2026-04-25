"""Tests for About dialog content."""

import unittest

from vvrite import __version__
from vvrite.main import (
    FORK_REPOSITORY_URL,
    ORIGINAL_REPOSITORY_URL,
    _about_message,
)


class TestAboutDialogContent(unittest.TestCase):
    def test_about_message_includes_version_and_both_repositories(self):
        message = _about_message()

        self.assertIn(__version__, message)
        self.assertIn(FORK_REPOSITORY_URL, message)
        self.assertIn(ORIGINAL_REPOSITORY_URL, message)
        self.assertIn("on-device voice transcription", message)


if __name__ == "__main__":
    unittest.main()
