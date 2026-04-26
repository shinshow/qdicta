"""Tests for clipboard helper functions."""

import unittest
from unittest.mock import MagicMock, patch

from Quartz import kCGEventFlagMaskCommand

from vvrite import clipboard


class TestClipboardHelpers(unittest.TestCase):
    @patch("vvrite.clipboard._post_keypress")
    def test_simulate_cmd_v_uses_command_modifier(self, mock_post_keypress):
        clipboard._simulate_cmd_v()

        mock_post_keypress.assert_called_once_with(
            clipboard.kVK_ANSI_V, kCGEventFlagMaskCommand
        )

    @patch("vvrite.clipboard._simulate_delete_backward")
    def test_retract_text_sends_delete_for_each_character(self, mock_delete):
        text = "한글 abc\n"

        result = clipboard.retract_text(text)

        self.assertTrue(result)
        mock_delete.assert_called_once_with(len(text))

    @patch("vvrite.clipboard._simulate_delete_backward")
    def test_retract_text_ignores_empty_text(self, mock_delete):
        self.assertFalse(clipboard.retract_text(""))
        mock_delete.assert_not_called()

    @patch("vvrite.clipboard.threading.Timer")
    @patch("vvrite.clipboard.restore")
    @patch("vvrite.clipboard._simulate_cmd_v")
    @patch("vvrite.clipboard._set_text")
    @patch("vvrite.clipboard.backup", return_value=[{"public.utf8-plain-text": b"old"}])
    @patch("vvrite.clipboard.time.sleep")
    def test_paste_and_restore_can_restore_clipboard_asynchronously(
        self,
        mock_sleep,
        _mock_backup,
        _mock_set_text,
        _mock_cmd_v,
        mock_restore,
        mock_timer,
    ):
        timer = MagicMock()
        mock_timer.return_value = timer

        clipboard.paste_and_restore("hello", async_restore=True)

        mock_sleep.assert_called_once_with(0.05)
        mock_restore.assert_not_called()
        mock_timer.assert_called_once_with(
            clipboard.CLIPBOARD_RESTORE_DELAY,
            clipboard.restore,
            args=([{"public.utf8-plain-text": b"old"}],),
        )
        self.assertTrue(timer.daemon)
        timer.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
