# Sound Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add customizable sound selection (system sounds + custom files) and per-sound volume control to the Settings window.

**Architecture:** Extend `sounds.py` with volume, custom file support, and system sound enumeration. Add `start_volume`/`stop_volume` preferences. Add a Sound section to the Settings UI with dropdowns and sliders. Wire `main.py` to pass volume to playback calls.

**Tech Stack:** Python, PyObjC (NSSound, NSSlider, NSPopUpButton, NSOpenPanel), unittest

**Spec:** `docs/superpowers/specs/2026-03-24-sound-settings-design.md`

---

### File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `vvrite/sounds.py` | Modify | Add `volume` param, custom file playback, `is_custom_path()`, `list_system_sounds()` |
| `vvrite/preferences.py` | Modify | Add `start_volume`, `stop_volume` properties |
| `vvrite/main.py` | Modify | Pass volume to `sounds.play()` calls |
| `vvrite/settings.py` | Modify | Add Sound section UI (dropdowns, sliders, auto-preview) |
| `tests/test_sounds.py` | Create | Tests for sounds module |
| `tests/test_preferences.py` | Modify | Add tests for volume preferences |

---

### Task 1: Extend sounds.py — is_custom_path and list_system_sounds

**Files:**
- Modify: `vvrite/sounds.py`
- Create: `tests/test_sounds.py`

- [ ] **Step 1: Write tests for `is_custom_path` and `list_system_sounds`**

```python
"""Tests for sounds module."""
import unittest


class TestIsCustomPath(unittest.TestCase):
    def test_system_sound_name(self):
        from vvrite.sounds import is_custom_path
        self.assertFalse(is_custom_path("Glass"))

    def test_absolute_path(self):
        from vvrite.sounds import is_custom_path
        self.assertTrue(is_custom_path("/Users/foo/beep.wav"))

    def test_empty_string(self):
        from vvrite.sounds import is_custom_path
        self.assertFalse(is_custom_path(""))


class TestListSystemSounds(unittest.TestCase):
    def test_returns_sorted_list(self):
        from vvrite.sounds import list_system_sounds
        sounds = list_system_sounds()
        self.assertIsInstance(sounds, list)
        self.assertEqual(sounds, sorted(sounds))

    def test_contains_known_sounds(self):
        from vvrite.sounds import list_system_sounds
        sounds = list_system_sounds()
        # These are standard macOS system sounds
        self.assertIn("Glass", sounds)
        self.assertIn("Purr", sounds)

    def test_no_file_extensions(self):
        from vvrite.sounds import list_system_sounds
        sounds = list_system_sounds()
        for name in sounds:
            self.assertFalse(name.endswith(".aiff"), f"{name} has extension")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_sounds -v`
Expected: FAIL — `is_custom_path` and `list_system_sounds` not defined

- [ ] **Step 3: Implement `is_custom_path` and `list_system_sounds`**

In `vvrite/sounds.py`, add at the top (after the existing import):

```python
import os

SYSTEM_SOUNDS_DIR = "/System/Library/Sounds"


def is_custom_path(name: str) -> bool:
    """Return True if name is a file path rather than a system sound name."""
    return "/" in name


def list_system_sounds() -> list[str]:
    """Return sorted list of macOS system sound names (without extension)."""
    if not os.path.isdir(SYSTEM_SOUNDS_DIR):
        return []
    names = []
    for entry in os.listdir(SYSTEM_SOUNDS_DIR):
        if entry.endswith(".aiff"):
            names.append(entry[:-5])  # strip .aiff
    return sorted(names)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_sounds -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add vvrite/sounds.py tests/test_sounds.py
git commit -m "Add is_custom_path and list_system_sounds to sounds module"
```

---

### Task 2: Extend sounds.py — volume and custom file playback

**Files:**
- Modify: `vvrite/sounds.py`
- Modify: `tests/test_sounds.py`

- [ ] **Step 1: Write tests for `play` with volume and custom path**

Append to `tests/test_sounds.py`:

```python
from unittest.mock import patch, MagicMock


class TestPlay(unittest.TestCase):
    @patch("vvrite.sounds.NSSound")
    def test_play_system_sound_with_volume(self, mock_nssound):
        from vvrite.sounds import play
        mock_sound = MagicMock()
        mock_copy = MagicMock()
        mock_sound.copy.return_value = mock_copy
        mock_nssound.soundNamed_.return_value = mock_sound

        play("Glass", volume=0.5)

        mock_nssound.soundNamed_.assert_called_once_with("Glass")
        mock_sound.copy.assert_called_once()
        mock_copy.setVolume_.assert_called_once_with(0.5)
        mock_copy.play.assert_called_once()

    @patch("vvrite.sounds.NSSound")
    def test_play_custom_file(self, mock_nssound):
        from vvrite.sounds import play
        mock_sound = MagicMock()
        mock_nssound.alloc.return_value.initWithContentsOfFile_byReference_.return_value = mock_sound

        play("/Users/foo/beep.wav", volume=0.7)

        mock_nssound.alloc.return_value.initWithContentsOfFile_byReference_.assert_called_once_with(
            "/Users/foo/beep.wav", True
        )
        mock_sound.setVolume_.assert_called_once_with(0.7)
        mock_sound.play.assert_called_once()

    @patch("vvrite.sounds.NSSound")
    def test_play_system_sound_not_found(self, mock_nssound):
        from vvrite.sounds import play
        mock_nssound.soundNamed_.return_value = None

        # Should not raise
        play("NonexistentSound", volume=1.0)

    @patch("vvrite.sounds.NSSound")
    def test_play_default_volume_is_one(self, mock_nssound):
        from vvrite.sounds import play
        mock_sound = MagicMock()
        mock_copy = MagicMock()
        mock_sound.copy.return_value = mock_copy
        mock_nssound.soundNamed_.return_value = mock_sound

        play("Glass")

        mock_copy.setVolume_.assert_called_once_with(1.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_sounds.TestPlay -v`
Expected: FAIL — `play` function signature doesn't accept `volume`

- [ ] **Step 3: Rewrite `play` function in `vvrite/sounds.py`**

Replace the existing `play` function:

```python
def play(name: str, volume: float = 1.0):
    """Play a sound by system name or file path, at the given volume (0.0–1.0)."""
    if is_custom_path(name):
        sound = NSSound.alloc().initWithContentsOfFile_byReference_(name, True)
    else:
        shared = NSSound.soundNamed_(name)
        if shared is None:
            return
        sound = shared.copy()
    if sound is None:
        return
    sound.setVolume_(volume)
    sound.play()
```

- [ ] **Step 4: Run all sounds tests**

Run: `python -m unittest tests.test_sounds -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add vvrite/sounds.py tests/test_sounds.py
git commit -m "Add volume control and custom file playback to sounds.play"
```

---

### Task 3: Add volume preferences

**Files:**
- Modify: `vvrite/preferences.py`
- Modify: `tests/test_preferences.py`

- [ ] **Step 1: Write tests for volume preferences**

Append to `tests/test_preferences.py`, inside the `TestPreferences` class. Also add `"start_volume"` and `"stop_volume"` to the `_TEST_KEYS` list at the top of the file.

```python
    def test_default_start_volume(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.start_volume, 1.0)

    def test_default_stop_volume(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.stop_volume, 1.0)

    def test_set_start_volume(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.start_volume = 0.5
        self.assertAlmostEqual(prefs.start_volume, 0.5)

    def test_set_stop_volume(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.stop_volume = 0.3
        self.assertAlmostEqual(prefs.stop_volume, 0.3)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_preferences.TestPreferences.test_default_start_volume -v`
Expected: FAIL — `start_volume` property not defined

- [ ] **Step 3: Add volume properties to preferences.py**

In `_DEFAULTS` dict, add before `"onboarding_completed"`:

```python
    "start_volume": 1.0,
    "stop_volume": 1.0,
```

Add property accessors after the `sound_stop` setter:

```python
    @property
    def start_volume(self) -> float:
        return float(self._get("start_volume"))

    @start_volume.setter
    def start_volume(self, value: float):
        self._set("start_volume", value)

    @property
    def stop_volume(self) -> float:
        return float(self._get("stop_volume"))

    @stop_volume.setter
    def stop_volume(self, value: float):
        self._set("stop_volume", value)
```

- [ ] **Step 4: Run all preference tests**

Run: `python -m unittest tests.test_preferences -v`
Expected: All tests PASS (existing + 4 new)

- [ ] **Step 5: Commit**

```bash
git add vvrite/preferences.py tests/test_preferences.py
git commit -m "Add start_volume and stop_volume preferences"
```

---

### Task 4: Wire volume into main.py

**Files:**
- Modify: `vvrite/main.py`

- [ ] **Step 1: Update `_start_recording` to pass volume**

In `vvrite/main.py`, change line 194:

```python
# Before:
sounds.play(self._prefs.sound_start)

# After:
sounds.play(self._prefs.sound_start, self._prefs.start_volume)
```

- [ ] **Step 2: Update `_stop_recording` to pass volume**

In `vvrite/main.py`, change line 218:

```python
# Before:
sounds.play(self._prefs.sound_stop)

# After:
sounds.play(self._prefs.sound_stop, self._prefs.stop_volume)
```

- [ ] **Step 3: Run existing tests to verify nothing breaks**

Run: `python -m unittest discover tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add vvrite/main.py
git commit -m "Pass volume to sounds.play in recording start/stop"
```

---

### Task 5: Add Sound section to Settings window

**Files:**
- Modify: `vvrite/settings.py`

This is the largest task. It adds the Sound section UI with two rows (start/stop), each containing a sound dropdown, volume slider, and percentage label.

- [ ] **Step 1: Add NSSlider and NSOpenPanel imports**

At the top of `vvrite/settings.py`, add to the AppKit imports:

```python
from AppKit import NSSlider, NSOpenPanel, NSMenuItem
```

Add `import os` and the sounds import:

```python
import os
from vvrite import sounds
```

- [ ] **Step 2: Add instance variables in `initWithPreferences_`**

Add after the existing `_custom_words_field = None` line:

```python
self._start_sound_popup = None
self._stop_sound_popup = None
self._start_volume_slider = None
self._stop_volume_slider = None
self._start_volume_label = None
self._stop_volume_label = None
```

- [ ] **Step 3: Increase window height**

Change the frame height from 586 to 706 (the Sound section adds ~120pt: 40 header + 30 start row + 30 stop row + 20 hint):

```python
frame = NSMakeRect(0, 0, 400, 706)
```

Update the initial y value from 572 to 692:

```python
y = 692
```

- [ ] **Step 4: Add Sound section UI in `_build_window`**

Insert the following block between the Custom Words hint and the Permissions section (after the "인식이 잘 안 되는 단어를" hint):

```python
        # --- Sound ---
        y -= 40
        label = NSTextField.labelWithString_("Sound")
        label.setFrame_(NSMakeRect(20, y, 360, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        content.addSubview_(label)

        # Start sound row
        y -= 30
        start_label = NSTextField.labelWithString_("Start")
        start_label.setFrame_(NSMakeRect(20, y, 50, 20))
        start_label.setAlignment_(2)  # NSTextAlignmentRight
        start_label.setTextColor_(NSColor.secondaryLabelColor())
        start_label.setFont_(NSFont.systemFontOfSize_(12.0))
        content.addSubview_(start_label)

        self._start_sound_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(76, y, 140, 24), False
        )
        self._start_sound_popup.setTarget_(self)
        self._start_sound_popup.setAction_("startSoundChanged:")
        content.addSubview_(self._start_sound_popup)

        self._start_volume_slider = NSSlider.alloc().initWithFrame_(
            NSMakeRect(222, y, 120, 24)
        )
        self._start_volume_slider.setMinValue_(0)
        self._start_volume_slider.setMaxValue_(100)
        self._start_volume_slider.setIntValue_(int(self._prefs.start_volume * 100))
        self._start_volume_slider.setContinuous_(True)
        self._start_volume_slider.setTarget_(self)
        self._start_volume_slider.setAction_("startVolumeChanged:")
        content.addSubview_(self._start_volume_slider)

        self._start_volume_label = NSTextField.labelWithString_(
            f"{int(self._prefs.start_volume * 100)}%"
        )
        self._start_volume_label.setFrame_(NSMakeRect(348, y, 40, 20))
        self._start_volume_label.setTextColor_(NSColor.secondaryLabelColor())
        self._start_volume_label.setFont_(NSFont.systemFontOfSize_(11.0))
        content.addSubview_(self._start_volume_label)

        # Stop sound row
        y -= 30
        stop_label = NSTextField.labelWithString_("Stop")
        stop_label.setFrame_(NSMakeRect(20, y, 50, 20))
        stop_label.setAlignment_(2)  # NSTextAlignmentRight
        stop_label.setTextColor_(NSColor.secondaryLabelColor())
        stop_label.setFont_(NSFont.systemFontOfSize_(12.0))
        content.addSubview_(stop_label)

        self._stop_sound_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(76, y, 140, 24), False
        )
        self._stop_sound_popup.setTarget_(self)
        self._stop_sound_popup.setAction_("stopSoundChanged:")
        content.addSubview_(self._stop_sound_popup)

        self._stop_volume_slider = NSSlider.alloc().initWithFrame_(
            NSMakeRect(222, y, 120, 24)
        )
        self._stop_volume_slider.setMinValue_(0)
        self._stop_volume_slider.setMaxValue_(100)
        self._stop_volume_slider.setIntValue_(int(self._prefs.stop_volume * 100))
        self._stop_volume_slider.setContinuous_(True)
        self._stop_volume_slider.setTarget_(self)
        self._stop_volume_slider.setAction_("stopVolumeChanged:")
        content.addSubview_(self._stop_volume_slider)

        self._stop_volume_label = NSTextField.labelWithString_(
            f"{int(self._prefs.stop_volume * 100)}%"
        )
        self._stop_volume_label.setFrame_(NSMakeRect(348, y, 40, 20))
        self._stop_volume_label.setTextColor_(NSColor.secondaryLabelColor())
        self._stop_volume_label.setFont_(NSFont.systemFontOfSize_(11.0))
        content.addSubview_(self._stop_volume_label)

        y -= 20
        hint = NSTextField.labelWithString_(
            "슬라이더를 조절하면 선택된 소리가 자동으로 재생됩니다"
        )
        hint.setFrame_(NSMakeRect(76, y, 310, 16))
        hint.setFont_(NSFont.systemFontOfSize_(11.0))
        hint.setTextColor_(NSColor.secondaryLabelColor())
        content.addSubview_(hint)

        self._populate_sounds()
```

- [ ] **Step 5: Add `_populate_sounds` method**

```python
    def _populate_sounds(self):
        """Populate both sound dropdowns with system sounds + Custom option."""
        system_sounds = sounds.list_system_sounds()
        for popup, pref_value in [
            (self._start_sound_popup, self._prefs.sound_start),
            (self._stop_sound_popup, self._prefs.sound_stop),
        ]:
            popup.removeAllItems()
            for name in system_sounds:
                popup.addItemWithTitle_(name)
            popup.menu().addItem_(NSMenuItem.separatorItem())
            popup.addItemWithTitle_("Custom...")

            # Select current value
            if sounds.is_custom_path(pref_value):
                filename = os.path.basename(pref_value)
                if filename:  # guard against empty/malformed paths
                    popup.insertItemWithTitle_atIndex_(filename, len(system_sounds))
                    popup.selectItemAtIndex_(len(system_sounds))
            else:
                idx = popup.indexOfItemWithTitle_(pref_value)
                if idx >= 0:
                    popup.selectItemAtIndex_(idx)
```

Note: `import os` and `NSMenuItem` are added in Step 1 (imports).

- [ ] **Step 6: Add `showWindow_` refresh call**

In the existing `showWindow_` method, add `self._populate_sounds()` after `self._populate_mics()`:

```python
    def showWindow_(self, sender):
        self._populate_mics()
        self._populate_sounds()
        self._window.makeKeyAndOrderFront_(sender)
        ...
```

- [ ] **Step 7: Add sound changed action handlers**

```python
    @objc.typedSelector(b"v@:@")
    def startSoundChanged_(self, sender):
        title = sender.titleOfSelectedItem()
        if title == "Custom...":
            self._open_custom_sound_panel(for_start=True)
            return
        self._prefs.sound_start = title
        sounds.play(title, self._prefs.start_volume)

    @objc.typedSelector(b"v@:@")
    def stopSoundChanged_(self, sender):
        title = sender.titleOfSelectedItem()
        if title == "Custom...":
            self._open_custom_sound_panel(for_start=False)
            return
        self._prefs.sound_stop = title
        sounds.play(title, self._prefs.stop_volume)
```

- [ ] **Step 8: Add volume changed action handlers**

```python
    @objc.typedSelector(b"v@:@")
    def startVolumeChanged_(self, sender):
        vol = sender.intValue() / 100.0
        self._prefs.start_volume = vol
        self._start_volume_label.setStringValue_(f"{sender.intValue()}%")
        # Play preview only on mouse-up (NSEventTypeLeftMouseUp == 2)
        event = NSApp.currentEvent()
        if event and event.type() == 2:
            sounds.play(self._prefs.sound_start, vol)

    @objc.typedSelector(b"v@:@")
    def stopVolumeChanged_(self, sender):
        vol = sender.intValue() / 100.0
        self._prefs.stop_volume = vol
        self._stop_volume_label.setStringValue_(f"{sender.intValue()}%")
        # Play preview only on mouse-up (NSEventTypeLeftMouseUp == 2)
        event = NSApp.currentEvent()
        if event and event.type() == 2:
            sounds.play(self._prefs.sound_stop, vol)
```

- [ ] **Step 9: Add custom sound file picker**

```python
    def _open_custom_sound_panel(self, for_start: bool):
        import UniformTypeIdentifiers
        panel = NSOpenPanel.openPanel()
        allowed_types = [
            UniformTypeIdentifiers.UTType.typeWithFilenameExtension_(ext)
            for ext in ["aiff", "wav", "mp3", "m4a", "caf"]
        ]
        panel.setAllowedContentTypes_(allowed_types)
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setTitle_("Choose a sound file")

        if panel.runModal() == 1:  # NSModalResponseOK
            path = str(panel.URL().path())
            if for_start:
                self._prefs.sound_start = path
                sounds.play(path, self._prefs.start_volume)
            else:
                self._prefs.sound_stop = path
                sounds.play(path, self._prefs.stop_volume)
            self._populate_sounds()
        else:
            # User cancelled — revert dropdown to current selection
            self._populate_sounds()
```

- [ ] **Step 10: Run all tests**

Run: `python -m unittest discover tests/ -v`
Expected: All tests PASS

- [ ] **Step 11: Commit**

```bash
git add vvrite/settings.py
git commit -m "Add Sound section to Settings with dropdowns, sliders, and auto-preview"
```

---

### Task 6: Manual smoke test

**Files:** None (verification only)

- [ ] **Step 1: Run the app**

Run: `python -m vvrite`

- [ ] **Step 2: Verify Sound section in Settings**

Open Settings from the menu bar. Verify:
- Sound section appears between Custom Words and Permissions
- Start dropdown shows system sounds with "Glass" selected
- Stop dropdown shows system sounds with "Purr" selected
- Both sliders are at 100%

- [ ] **Step 3: Test sound selection**

- Change Start sound to "Pop" → hear "Pop" play immediately
- Change Stop sound to "Tink" → hear "Tink" play immediately
- Select "Custom..." → file picker opens, select a .wav file → hear it play

- [ ] **Step 4: Test volume sliders**

- Drag Start slider to 50% → percentage label updates during drag → sound plays on release
- Drag Stop slider to 0% → no sound on release
- Drag slider back to 100% → sound plays at full volume

- [ ] **Step 5: Test recording flow**

- Press hotkey → hear start sound at configured volume
- Press hotkey again → hear stop sound at configured volume
- Verify transcription still works normally

- [ ] **Step 6: Test persistence**

- Quit and reopen app
- Open Settings → verify sound selections and volumes are preserved

- [ ] **Step 7: Commit if any fixes were needed**

```bash
git add -u
git commit -m "Fix issues found during smoke test"
```
