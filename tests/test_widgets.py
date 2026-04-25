"""Tests for shortcut capture widgets."""

import unittest

from AppKit import NSEventModifierFlagCommand, NSEventModifierFlagShift
from Foundation import NSUserDefaults
from Quartz import kCGEventFlagMaskCommand, kCGEventFlagMaskShift

from vvrite.preferences import APP_DEFAULTS_DOMAIN
from vvrite.widgets import ShortcutField

_TEST_KEYS = [
    "hotkey_keycode",
    "hotkey_modifiers",
]
_LEGACY_DOMAINS = ["com.vvrite.app", "python3", "python", "Python"]


class _FakeEvent:
    def __init__(self, keycode, modifiers):
        self._keycode = keycode
        self._modifiers = modifiers

    def keyCode(self):
        return self._keycode

    def modifierFlags(self):
        return self._modifiers


class _Prefs:
    hotkey_keycode = 0x31
    hotkey_modifiers = 0


class TestShortcutField(unittest.TestCase):
    def setUp(self):
        defaults = NSUserDefaults.standardUserDefaults()
        for key in _TEST_KEYS:
            defaults.removeObjectForKey_(key)
        defaults.removePersistentDomainForName_(APP_DEFAULTS_DOMAIN)
        for domain in _LEGACY_DOMAINS:
            defaults.removePersistentDomainForName_(domain)

    def tearDown(self):
        defaults = NSUserDefaults.standardUserDefaults()
        for key in _TEST_KEYS:
            defaults.removeObjectForKey_(key)
        defaults.removePersistentDomainForName_(APP_DEFAULTS_DOMAIN)
        for domain in _LEGACY_DOMAINS:
            defaults.removePersistentDomainForName_(domain)

    def test_perform_key_equivalent_captures_command_shortcut(self):
        field = ShortcutField.alloc().initWithFrame_preferences_(
            ((0, 0), (200, 24)), _Prefs()
        )
        field._capturing = True

        handled = field.performKeyEquivalent_(
            _FakeEvent(
                0x00,
                NSEventModifierFlagCommand | NSEventModifierFlagShift,
            )
        )

        self.assertTrue(handled)
        self.assertEqual(field._prefs.hotkey_keycode, 0x00)
        self.assertEqual(
            field._prefs.hotkey_modifiers,
            int(kCGEventFlagMaskCommand | kCGEventFlagMaskShift),
        )
        self.assertFalse(field._capturing)


if __name__ == "__main__":
    unittest.main()
