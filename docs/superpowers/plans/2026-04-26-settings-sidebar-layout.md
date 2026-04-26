# Settings Sidebar Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the oversized single-column settings window with a compact sidebar-driven layout that is usable on smaller Mac screens.

**Architecture:** Keep `SettingsWindowController` as the owner of the window, preferences, and existing action methods. Split UI construction into a fixed left sidebar and a scrollable right content pane, with one builder method per settings category. Reuse the current manual AppKit frame style to avoid mixing layout systems in this pass.

**Tech Stack:** Python, PyObjC AppKit (`NSWindow`, `NSButton`, `NSScrollView`, `NSView`, existing controls), `unittest`.

---

## File Structure

- Modify `vvrite/settings.py`
  - Add compact layout constants.
  - Add sidebar category metadata.
  - Build a fixed-height window with a left sidebar and right scroll view.
  - Split current control construction into category builder methods.
  - Keep existing action methods and preference writes.
- Modify `vvrite/locales/*.py`
  - Add sidebar category title strings.
- Modify `tests/test_settings.py`
  - Add tests for compact height, category metadata/order, switching categories, and scroll content replacement.
  - Update old height test expectations.
- Modify `tests/test_locales.py`
  - Add completeness checks for `settings.categories`.

---

## Task 1: Add Sidebar Locale Keys And Category Metadata

**Files:**
- Modify: `vvrite/settings.py`
- Modify: `vvrite/locales/*.py`
- Modify: `tests/test_settings.py`
- Modify: `tests/test_locales.py`

- [ ] **Step 1: Write failing settings category tests**

Add these tests to `tests/test_settings.py` near the existing `TestAsrModelSettingsActions` class:

```python
class TestSettingsSidebarLayout(unittest.TestCase):
    def test_settings_window_height_is_small_screen_friendly(self):
        from vvrite.settings import SETTINGS_WINDOW_HEIGHT

        self.assertLessEqual(SETTINGS_WINDOW_HEIGHT, 700)

    def test_sidebar_categories_are_in_expected_order(self):
        from vvrite.settings import SETTINGS_CATEGORIES

        self.assertEqual(
            [category.key for category in SETTINGS_CATEGORIES],
            ["general", "recording", "model", "output", "sound", "advanced"],
        )
```

- [ ] **Step 2: Write failing locale completeness test**

In `tests/test_locales.py`, inside `TestEnglishStringsCompleteness.test_settings_keys`, add this after the existing `settings.mode` check:

```python
        # categories
        self.assertIn("categories", s)
        for key in ["general", "recording", "model", "output", "sound", "advanced"]:
            self.assertIn(key, s["categories"], f"Missing settings.categories.{key}")
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_settings.TestSettingsSidebarLayout \
  tests.test_locales.TestEnglishStringsCompleteness.test_settings_keys
```

Expected:
- `SETTINGS_WINDOW_HEIGHT` is still too large.
- `SETTINGS_CATEGORIES` is missing.
- `settings.categories` is missing.

- [ ] **Step 4: Add layout constants and category metadata**

In `vvrite/settings.py`, update constants and add a dataclass near the constants:

```python
from dataclasses import dataclass
```

```python
SETTINGS_WINDOW_WIDTH = 640
SETTINGS_WINDOW_HEIGHT = 660
SETTINGS_SIDEBAR_WIDTH = 170
SETTINGS_CONTENT_WIDTH = SETTINGS_WINDOW_WIDTH - SETTINGS_SIDEBAR_WIDTH
SETTINGS_CONTENT_HEIGHT = SETTINGS_WINDOW_HEIGHT
SETTINGS_START_Y = SETTINGS_CONTENT_HEIGHT - 24


@dataclass(frozen=True)
class SettingsCategory:
    key: str
    title_key: str


SETTINGS_CATEGORIES = [
    SettingsCategory("general", "settings.categories.general"),
    SettingsCategory("recording", "settings.categories.recording"),
    SettingsCategory("model", "settings.categories.model"),
    SettingsCategory("output", "settings.categories.output"),
    SettingsCategory("sound", "settings.categories.sound"),
    SettingsCategory("advanced", "settings.categories.advanced"),
]
```

Remove the old `SETTINGS_WINDOW_HEIGHT = 1160` and old `SETTINGS_START_Y = SETTINGS_WINDOW_HEIGHT - 14`.

- [ ] **Step 5: Add English locale keys**

In `vvrite/locales/en.py`, inside the top-level `settings` dict, add:

```python
        "categories": {
            "general": "General",
            "recording": "Recording",
            "model": "Model",
            "output": "Output",
            "sound": "Sound",
            "advanced": "Advanced",
        },
```

- [ ] **Step 6: Add category keys to all other locale files**

Add the same `settings.categories` keys to every locale file. Use English labels if the translated label is uncertain:

```python
        "categories": {
            "general": "General",
            "recording": "Recording",
            "model": "Model",
            "output": "Output",
            "sound": "Sound",
            "advanced": "Advanced",
        },
```

- [ ] **Step 7: Run tests**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_settings.TestSettingsSidebarLayout \
  tests.test_locales
```

Expected: `OK`.

- [ ] **Step 8: Commit**

```bash
git add vvrite/settings.py vvrite/locales tests/test_settings.py tests/test_locales.py
git commit -m "feat: define settings sidebar categories"
```

---

## Task 2: Build Compact Window Shell With Sidebar And Scroll Pane

**Files:**
- Modify: `vvrite/settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write failing shell construction tests**

Add these tests to `TestSettingsSidebarLayout` in `tests/test_settings.py`:

```python
    @patch("vvrite.settings.transcriber.is_model_cached", return_value=False)
    @patch("vvrite.settings.list_input_devices", return_value=[])
    @patch("vvrite.settings.sounds.list_system_sounds", return_value=["Tink", "Purr"])
    def test_settings_window_builds_sidebar_and_content_scroll_view(
        self, _mock_sounds, _mock_devices, _mock_cached
    ):
        from vvrite.preferences import Preferences

        controller = SettingsWindowController.alloc().initWithPreferences_(Preferences())

        self.assertIsNotNone(controller._sidebar_view)
        self.assertIsNotNone(controller._content_scroll)
        self.assertIsNotNone(controller._content_container)
        self.assertEqual(controller._selected_category_key, "general")

    def test_selecting_category_replaces_content_container(self):
        controller = SettingsWindowController.alloc().init()
        controller._prefs = MagicMock()
        controller._content_scroll = MagicMock()
        controller._category_builders = {
            "general": lambda: MagicMock(name="general_view"),
            "sound": lambda: MagicMock(name="sound_view"),
        }

        controller._show_settings_category("general")
        first = controller._content_container
        controller._show_settings_category("sound")

        self.assertIsNot(controller._content_container, first)
        self.assertEqual(controller._selected_category_key, "sound")
        controller._content_scroll.setDocumentView_.assert_called_with(
            controller._content_container
        )
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings.TestSettingsSidebarLayout
```

Expected:
- `_sidebar_view`, `_content_scroll`, `_content_container`, or `_show_settings_category` missing.

- [ ] **Step 3: Add imports**

In `vvrite/settings.py`, add `NSView` to the `from AppKit import (...)` import list:

```python
    NSView,
```

- [ ] **Step 4: Add controller fields**

In `SettingsWindowController.initWithPreferences_`, after `self._window = None`, add:

```python
        self._sidebar_view = None
        self._content_scroll = None
        self._content_container = None
        self._selected_category_key = None
        self._sidebar_buttons = {}
        self._category_builders = {}
```

- [ ] **Step 5: Replace `_build_window` shell setup**

At the start of `_build_window`, replace the old frame and `content/y` setup with this shell:

```python
        frame = NSMakeRect(0, 0, SETTINGS_WINDOW_WIDTH, SETTINGS_WINDOW_HEIGHT)
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_(t("settings.title"))
        self._window.setReleasedWhenClosed_(False)
        self._window.center()
        self._window.setDelegate_(self)

        content = self._window.contentView()
        self._sidebar_view = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, SETTINGS_SIDEBAR_WIDTH, SETTINGS_WINDOW_HEIGHT)
        )
        content.addSubview_(self._sidebar_view)

        self._content_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(
                SETTINGS_SIDEBAR_WIDTH,
                0,
                SETTINGS_CONTENT_WIDTH,
                SETTINGS_WINDOW_HEIGHT,
            )
        )
        self._content_scroll.setHasVerticalScroller_(True)
        self._content_scroll.setAutohidesScrollers_(True)
        self._content_scroll.setBorderType_(0)
        content.addSubview_(self._content_scroll)

        self._build_sidebar()
        self._category_builders = {
            "general": self._build_general_panel,
            "recording": self._build_recording_panel,
            "model": self._build_model_panel,
            "output": self._build_output_panel,
            "sound": self._build_sound_panel,
            "advanced": self._build_advanced_panel,
        }
        self._show_settings_category("general")
        self._update_permissions()
        self._refresh_login_checkbox()
        self._refresh_retract_controls()
        return
```

Keep the old single-column code below temporarily. The `return` prevents it from running while tasks migrate panels.

- [ ] **Step 6: Add sidebar builder and category switcher**

Add these methods before `_populate_sounds`:

```python
    def _build_sidebar(self):
        self._sidebar_buttons = {}
        y = SETTINGS_WINDOW_HEIGHT - 50
        for category in SETTINGS_CATEGORIES:
            button = NSButton.alloc().initWithFrame_(
                NSMakeRect(12, y, SETTINGS_SIDEBAR_WIDTH - 24, 28)
            )
            button.setTitle_(t(category.title_key))
            button.setBezelStyle_(NSBezelStyleRounded)
            button.setTarget_(self)
            button.setAction_("sidebarCategoryChanged:")
            button.setRepresentedObject_(category.key)
            self._sidebar_view.addSubview_(button)
            self._sidebar_buttons[category.key] = button
            y -= 34

    @objc.typedSelector(b"v@:@")
    def sidebarCategoryChanged_(self, sender):
        self._show_settings_category(str(sender.representedObject()))

    def _new_panel(self, height: int = SETTINGS_CONTENT_HEIGHT) -> tuple[object, int]:
        panel_height = max(height, SETTINGS_CONTENT_HEIGHT)
        panel = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, SETTINGS_CONTENT_WIDTH, panel_height)
        )
        return panel, panel_height - 24

    def _set_content_panel(self, panel):
        self._content_container = panel
        self._content_scroll.setDocumentView_(panel)

    def _show_settings_category(self, category_key: str):
        builder = self._category_builders.get(category_key)
        if builder is None:
            category_key = "general"
            builder = self._category_builders[category_key]
        self._selected_category_key = category_key
        panel = builder()
        self._set_content_panel(panel)
```

- [ ] **Step 7: Add temporary empty panel builders**

Add these methods before `_populate_sounds`:

```python
    def _build_general_panel(self):
        panel, y = self._new_panel()
        label = NSTextField.labelWithString_(t("settings.categories.general"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)
        return panel

    def _build_recording_panel(self):
        panel, y = self._new_panel()
        label = NSTextField.labelWithString_(t("settings.categories.recording"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)
        return panel

    def _build_model_panel(self):
        panel, y = self._new_panel()
        label = NSTextField.labelWithString_(t("settings.categories.model"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)
        return panel

    def _build_output_panel(self):
        panel, y = self._new_panel()
        label = NSTextField.labelWithString_(t("settings.categories.output"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)
        return panel

    def _build_sound_panel(self):
        panel, y = self._new_panel()
        label = NSTextField.labelWithString_(t("settings.categories.sound"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)
        return panel

    def _build_advanced_panel(self):
        panel, y = self._new_panel()
        label = NSTextField.labelWithString_(t("settings.categories.advanced"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)
        return panel
```

- [ ] **Step 8: Run tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings.TestSettingsSidebarLayout
```

Expected: `OK`.

- [ ] **Step 9: Commit**

```bash
git add vvrite/settings.py tests/test_settings.py
git commit -m "feat: add settings sidebar shell"
```

---

## Task 3: Move General And Recording Controls Into Panels

**Files:**
- Modify: `vvrite/settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write failing tests for General and Recording panels**

Add these tests to `TestSettingsSidebarLayout`:

```python
    @patch("vvrite.settings.list_input_devices", return_value=[])
    def test_general_panel_builds_language_and_login_controls(self, _mock_devices):
        from vvrite.preferences import Preferences

        controller = SettingsWindowController.alloc().initWithPreferences_(Preferences())
        controller._show_settings_category("general")

        self.assertIsNotNone(controller._ui_lang_popup)
        self.assertIsNotNone(controller._asr_lang_popup)
        self.assertIsNotNone(controller._login_checkbox)

    @patch("vvrite.settings.list_input_devices", return_value=[])
    def test_recording_panel_builds_hotkey_microphone_and_permission_controls(
        self, _mock_devices
    ):
        from vvrite.preferences import Preferences

        controller = SettingsWindowController.alloc().initWithPreferences_(Preferences())
        controller._show_settings_category("recording")

        self.assertIsNotNone(controller._shortcut_field)
        self.assertIsNotNone(controller._mic_popup)
        self.assertIsNotNone(controller._acc_label)
        self.assertIsNotNone(controller._mic_label)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings.TestSettingsSidebarLayout
```

Expected: The fields are `None` because panel builders are temporary labels.

- [ ] **Step 3: Implement `_build_general_panel`**

Replace `_build_general_panel` with:

```python
    def _build_general_panel(self):
        panel, y = self._new_panel()

        label = NSTextField.labelWithString_(t("settings.language.title"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)

        y -= 30
        ui_lang_label = NSTextField.labelWithString_(t("settings.language.ui_language"))
        ui_lang_label.setFrame_(NSMakeRect(20, y, 130, 20))
        ui_lang_label.setAlignment_(2)
        ui_lang_label.setTextColor_(NSColor.secondaryLabelColor())
        ui_lang_label.setFont_(NSFont.systemFontOfSize_(12.0))
        panel.addSubview_(ui_lang_label)

        self._ui_lang_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(156, y, 260, 24), False
        )
        self._ui_lang_popup.addItemWithTitle_(t("common.system_default"))
        for code, native_name in SUPPORTED_LANGUAGES:
            self._ui_lang_popup.addItemWithTitle_(native_name)
        current_ui = self._prefs.ui_language
        if current_ui is None:
            self._ui_lang_popup.selectItemAtIndex_(0)
        else:
            selected = 0
            for i, (code, _) in enumerate(SUPPORTED_LANGUAGES):
                if code == current_ui:
                    selected = i + 1
                    break
            self._ui_lang_popup.selectItemAtIndex_(selected)
        self._ui_lang_popup.setTarget_(self)
        self._ui_lang_popup.setAction_("uiLanguageChanged:")
        panel.addSubview_(self._ui_lang_popup)

        y -= 30
        asr_lang_label = NSTextField.labelWithString_(t("settings.language.asr_language"))
        asr_lang_label.setFrame_(NSMakeRect(20, y, 130, 20))
        asr_lang_label.setAlignment_(2)
        asr_lang_label.setTextColor_(NSColor.secondaryLabelColor())
        asr_lang_label.setFont_(NSFont.systemFontOfSize_(12.0))
        panel.addSubview_(asr_lang_label)

        self._asr_lang_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(156, y, 260, 24), False
        )
        self._asr_lang_popup.addItemWithTitle_(t("common.automatic"))
        for code, native_name in SUPPORTED_LANGUAGES:
            self._asr_lang_popup.addItemWithTitle_(native_name)
        current_asr = self._prefs.asr_language
        if current_asr == "auto":
            self._asr_lang_popup.selectItemAtIndex_(0)
        else:
            selected = 0
            for i, (code, _) in enumerate(SUPPORTED_LANGUAGES):
                if code == current_asr:
                    selected = i + 1
                    break
            self._asr_lang_popup.selectItemAtIndex_(selected)
        self._asr_lang_popup.setTarget_(self)
        self._asr_lang_popup.setAction_("asrLanguageChanged:")
        panel.addSubview_(self._asr_lang_popup)

        y -= 44
        self._login_checkbox = NSButton.alloc().initWithFrame_(
            NSMakeRect(20, y, 360, 20)
        )
        self._login_checkbox.setButtonType_(NSButtonTypeSwitch)
        self._login_checkbox.setTitle_(t("settings.login.title"))
        self._login_checkbox.setState_(1 if self._prefs.launch_at_login else 0)
        self._login_checkbox.setTarget_(self)
        self._login_checkbox.setAction_("loginToggled:")
        panel.addSubview_(self._login_checkbox)

        y -= 30
        update_checkbox = NSButton.alloc().initWithFrame_(
            NSMakeRect(20, y, 360, 20)
        )
        update_checkbox.setButtonType_(NSButtonTypeSwitch)
        update_checkbox.setTitle_(t("settings.update.title"))
        update_checkbox.setState_(1 if self._prefs.auto_update_check else 0)
        update_checkbox.setTarget_(self)
        update_checkbox.setAction_("autoUpdateCheckToggled:")
        panel.addSubview_(update_checkbox)

        return panel
```

- [ ] **Step 4: Add auto-update action if missing**

If `SettingsWindowController` does not already have `autoUpdateCheckToggled_`, add:

```python
    @objc.typedSelector(b"v@:@")
    def autoUpdateCheckToggled_(self, sender):
        self._prefs.auto_update_check = sender.state() == 1
```

- [ ] **Step 5: Implement `_build_recording_panel`**

Replace `_build_recording_panel` with:

```python
    def _build_recording_panel(self):
        panel, y = self._new_panel()

        label = NSTextField.labelWithString_(t("settings.shortcut.title"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)

        y -= 30
        self._shortcut_field = ShortcutField.alloc().initWithFrame_preferences_(
            NSMakeRect(20, y, 300, 24), self._prefs
        )
        self._shortcut_field._on_change = self._update_hotkey_display
        panel.addSubview_(self._shortcut_field)

        change_btn = NSButton.alloc().initWithFrame_(NSMakeRect(330, y, 80, 24))
        change_btn.setTitle_(t("common.change"))
        change_btn.setBezelStyle_(NSBezelStyleRounded)
        change_btn.setTarget_(self)
        change_btn.setAction_("changeShortcut:")
        panel.addSubview_(change_btn)

        y -= 44
        label = NSTextField.labelWithString_(t("settings.microphone.title"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)

        y -= 30
        self._mic_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(20, y, 390, 24), False
        )
        self._populate_mics(refresh=True)
        self._mic_popup.setTarget_(self)
        self._mic_popup.setAction_("micChanged:")
        panel.addSubview_(self._mic_popup)

        y -= 44
        label = NSTextField.labelWithString_(t("settings.permissions.title"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)

        y -= 26
        self._acc_label = NSTextField.labelWithString_(
            t("settings.permissions.accessibility_checking")
        )
        self._acc_label.setFrame_(NSMakeRect(20, y, 290, 20))
        panel.addSubview_(self._acc_label)

        acc_btn = NSButton.alloc().initWithFrame_(NSMakeRect(330, y, 80, 24))
        acc_btn.setTitle_(t("common.open"))
        acc_btn.setBezelStyle_(NSBezelStyleRounded)
        acc_btn.setTarget_(self)
        acc_btn.setAction_("openAccessibility:")
        panel.addSubview_(acc_btn)

        y -= 30
        self._mic_label = NSTextField.labelWithString_(
            t("settings.permissions.microphone_checking")
        )
        self._mic_label.setFrame_(NSMakeRect(20, y, 290, 20))
        panel.addSubview_(self._mic_label)

        mic_perm_btn = NSButton.alloc().initWithFrame_(NSMakeRect(330, y, 80, 24))
        mic_perm_btn.setTitle_(t("common.open"))
        mic_perm_btn.setBezelStyle_(NSBezelStyleRounded)
        mic_perm_btn.setTarget_(self)
        mic_perm_btn.setAction_("openMicrophonePrivacy:")
        panel.addSubview_(mic_perm_btn)

        self._update_permissions()
        return panel
```

- [ ] **Step 6: Make `_update_permissions` tolerate absent controls**

Replace `_update_permissions` body with:

```python
        trusted = ApplicationServices.AXIsProcessTrusted()
        if self._acc_label is not None:
            if trusted:
                self._acc_label.setStringValue_(
                    t("settings.permissions.accessibility_granted")
                )
            else:
                self._acc_label.setStringValue_(
                    t("settings.permissions.accessibility_not_granted")
                )
        if self._mic_label is not None:
            self._mic_label.setStringValue_(t("settings.permissions.microphone_granted"))
```

- [ ] **Step 7: Run tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings
```

Expected: `OK`.

- [ ] **Step 8: Commit**

```bash
git add vvrite/settings.py tests/test_settings.py
git commit -m "feat: move general and recording settings panels"
```

---

## Task 4: Move Model, Output, Sound, And Advanced Panels

**Files:**
- Modify: `vvrite/settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write failing tests for remaining panels**

Add these tests to `TestSettingsSidebarLayout`:

```python
    @patch("vvrite.settings.transcriber.is_model_cached", return_value=False)
    def test_model_panel_builds_model_controls(self, _mock_cached):
        from vvrite.preferences import Preferences

        controller = SettingsWindowController.alloc().initWithPreferences_(Preferences())
        controller._show_settings_category("model")

        self.assertIsNotNone(controller._model_popup)
        self.assertIsNotNone(controller._output_mode_popup)
        self.assertIsNotNone(controller._download_model_btn)
        self.assertIsNotNone(controller._delete_model_btn)

    def test_output_panel_builds_mode_and_text_controls(self):
        from vvrite.preferences import Preferences

        controller = SettingsWindowController.alloc().initWithPreferences_(Preferences())
        controller._show_settings_category("output")

        self.assertIsNotNone(controller._mode_popup)
        self.assertIsNotNone(controller._custom_words_text_view)
        self.assertIsNotNone(controller._replacement_rules_text_view)

    @patch("vvrite.settings.sounds.list_system_sounds", return_value=["Tink", "Purr"])
    def test_sound_panel_builds_sound_controls(self, _mock_sounds):
        from vvrite.preferences import Preferences

        controller = SettingsWindowController.alloc().initWithPreferences_(Preferences())
        controller._show_settings_category("sound")

        self.assertIsNotNone(controller._start_sound_popup)
        self.assertIsNotNone(controller._stop_sound_popup)
        self.assertIsNotNone(controller._start_volume_slider)
        self.assertIsNotNone(controller._stop_volume_slider)

    def test_advanced_panel_builds_retract_controls(self):
        from vvrite.preferences import Preferences

        controller = SettingsWindowController.alloc().initWithPreferences_(Preferences())
        controller._show_settings_category("advanced")

        self.assertIsNotNone(controller._retract_checkbox)
        self.assertIsNotNone(controller._retract_shortcut_field)
        self.assertIsNotNone(controller._retract_change_btn)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings.TestSettingsSidebarLayout
```

Expected: temporary label panel builders do not create these controls.

- [ ] **Step 3: Move model controls into `_build_model_panel`**

Move the existing model section code from old `_build_window` into `_build_model_panel`, adapting:

- Use `panel.addSubview_` instead of `content.addSubview_`.
- Use `SETTINGS_CONTENT_WIDTH - 40` for full-width labels.
- Keep existing calls to `_refresh_model_controls()`.
- Create these fields in the model panel:
  - `_model_popup`
  - `_output_mode_popup`
  - `_model_capability_label`
  - `_model_status_label`
  - `_download_model_btn`
  - `_delete_model_btn`
  - `_download_progress_bar`
  - `_download_progress_label`

The method should start:

```python
    def _build_model_panel(self):
        panel, y = self._new_panel()
        label = NSTextField.labelWithString_(t("settings.model.title"))
        label.setFrame_(NSMakeRect(20, y, SETTINGS_CONTENT_WIDTH - 40, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        panel.addSubview_(label)
        # continue with existing model controls
```

End with:

```python
        self._refresh_model_controls()
        return panel
```

- [ ] **Step 4: Move output controls into `_build_output_panel`**

Move the current Mode, Custom Words, and Replacements sections into `_build_output_panel`.

The method should create:

- `_mode_popup`
- `_custom_words_text_view`
- import/export custom word buttons
- `_replacement_rules_text_view`

Use a taller panel because this category has two text editors:

```python
        panel, y = self._new_panel(760)
```

End with:

```python
        return panel
```

- [ ] **Step 5: Move sound controls into `_build_sound_panel`**

Move the existing Sound section into `_build_sound_panel`.

The method should create:

- `_start_sound_popup`
- `_stop_sound_popup`
- `_start_volume_slider`
- `_stop_volume_slider`
- `_start_volume_label`
- `_stop_volume_label`

End with:

```python
        self._populate_sounds()
        return panel
```

- [ ] **Step 6: Move retract controls into `_build_advanced_panel`**

Move the current Advanced Correction section into `_build_advanced_panel`.

The method should create:

- `_retract_checkbox`
- `_retract_shortcut_field`
- `_retract_change_btn`

End with:

```python
        self._refresh_retract_controls()
        return panel
```

- [ ] **Step 7: Make panel-sensitive helpers tolerate absent controls**

Update these methods so they return early or skip absent controls:

```python
    def _populate_sounds(self):
        if self._start_sound_popup is None or self._stop_sound_popup is None:
            return
        # existing body
```

```python
    def _refresh_login_checkbox(self):
        if self._login_checkbox is None:
            return
        # existing body
```

```python
    def _refresh_retract_controls(self):
        if self._retract_checkbox is None:
            return
        # existing body
```

If `_refresh_model_controls` already uses `getattr(..., None)`, keep that pattern.

- [ ] **Step 8: Run settings tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings
```

Expected: `OK`.

- [ ] **Step 9: Commit**

```bash
git add vvrite/settings.py tests/test_settings.py
git commit -m "feat: split settings into sidebar panels"
```

---

## Task 5: Remove Old Single-Column Build Code And Finalize Refresh Behavior

**Files:**
- Modify: `vvrite/settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Add regression tests for show window refresh behavior**

Add these tests to `TestSettingsSidebarLayout`:

```python
    @patch("vvrite.settings.NSTimer")
    @patch("vvrite.settings.NSApp")
    def test_show_window_keeps_current_category_and_refreshes_shared_state(
        self, mock_app, _mock_timer
    ):
        controller = SettingsWindowController.alloc().init()
        controller._window = MagicMock()
        controller._adopt_single_downloaded_model_if_unset = MagicMock()
        controller._sync_model_controls_from_preferences = MagicMock()
        controller._populate_mics = MagicMock()
        controller._populate_sounds = MagicMock()
        controller._show_settings_category = MagicMock()
        controller._selected_category_key = "sound"

        controller.showWindow_(None)

        controller._show_settings_category.assert_called_once_with("sound")
        controller._populate_mics.assert_called_once_with(refresh=True)
        controller._populate_sounds.assert_called_once_with()
        controller._window.makeKeyAndOrderFront_.assert_called_once_with(None)
        mock_app.activateIgnoringOtherApps_.assert_called_once_with(True)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_settings.TestSettingsSidebarLayout.test_show_window_keeps_current_category_and_refreshes_shared_state
```

Expected: `_show_settings_category` may not be called by `showWindow_`.

- [ ] **Step 3: Update `showWindow_`**

Replace the top of `showWindow_` with:

```python
    def showWindow_(self, sender):
        self._adopt_single_downloaded_model_if_unset()
        self._sync_model_controls_from_preferences()
        current_category = self._selected_category_key or "general"
        self._show_settings_category(current_category)
        self._populate_mics(refresh=True)
        self._populate_sounds()
        self._window.makeKeyAndOrderFront_(sender)
        NSApp.activateIgnoringOtherApps_(True)
        self._permission_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            2.0, self, "pollPermissions:", None, True
        )
```

- [ ] **Step 4: Remove unreachable old `_build_window` body**

After the shell setup in `_build_window`, remove the old single-column code that is currently below the early `return`. The method should only contain:

- Window creation.
- Sidebar creation.
- Scroll view creation.
- Sidebar/category builder registration.
- Default category selection.
- Shared initial refresh calls.

- [ ] **Step 5: Verify no duplicate section comments remain inside `_build_window`**

Run:

```bash
rg -n "# --- Language ---|# --- Model ---|# --- Sound ---|# --- Launch at Login ---" vvrite/settings.py
```

Expected: section comments are only inside category builder methods, not after an early return in `_build_window`.

- [ ] **Step 6: Run settings tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings
```

Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add vvrite/settings.py tests/test_settings.py
git commit -m "refactor: remove legacy settings column layout"
```

---

## Task 6: Final Verification And Local Build

**Files:**
- No source edits expected.

- [ ] **Step 1: Run full unit tests**

Run:

```bash
.venv/bin/python -m unittest discover tests
```

Expected: `OK`.

- [ ] **Step 2: Run compile check**

Run:

```bash
.venv/bin/python -m compileall -q vvrite tests
```

Expected: exit code `0`.

- [ ] **Step 3: Run UI smoke**

Run:

```bash
.venv/bin/python -c $'from AppKit import NSApplication\napp=NSApplication.sharedApplication()\nfrom vvrite.preferences import Preferences\nfrom vvrite.settings import SettingsWindowController\nfrom vvrite.overlay import OverlayController\nwc=SettingsWindowController.alloc().initWithPreferences_(Preferences())\nov=OverlayController.alloc().init()\nprint("ui objects built", wc is not None, ov is not None)\n'
```

Expected:

```text
ui objects built True True
```

- [ ] **Step 4: Run local build**

Run:

```bash
./scripts/build.sh --local
```

Expected:

```text
✓ Done! dist/vvrite.dmg is ready for local testing.
```

- [ ] **Step 5: Confirm working tree is clean**

Run:

```bash
git status --short
```

Expected: no output.

---

## Self-Review

Spec coverage:
- Compact small-screen settings window: Task 1 and Task 2.
- Sidebar categories: Task 1 and Task 2.
- Scrollable right pane: Task 2.
- Category builders: Tasks 3 and 4.
- Existing action behavior preserved: Tasks 3, 4, and 5 keep action methods and extend tests.
- Final verification: Task 6.

Plan hygiene:
- No unresolved marker strings.
- All new tests and commands are specified.
- Panel migration steps identify exact controls and methods.

Type consistency:
- Category metadata uses `SettingsCategory.key` and `SettingsCategory.title_key`.
- Category switcher uses `_show_settings_category(category_key: str)`.
- Sidebar action uses `sidebarCategoryChanged_`, matching AppKit selector `"sidebarCategoryChanged:"`.
