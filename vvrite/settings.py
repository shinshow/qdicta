"""Settings window for hotkey, microphone, permissions, and launch at login."""

import objc
import ApplicationServices
from AppKit import (
    NSObject,
    NSMakeRect,
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSTextField,
    NSFont,
    NSButton,
    NSButtonTypeSwitch,
    NSPopUpButton,
    NSColor,
    NSApp,
    NSBezelStyleRounded,
    NSAlert,
    NSWorkspace,
)
from Foundation import NSLog, NSURL, NSTimer

from vvrite import launch_at_login
from vvrite.audio_devices import (
    get_default_input_device,
    list_input_devices,
    resolve_input_device,
)
from vvrite.preferences import Preferences
from vvrite.widgets import ShortcutField


class SettingsWindowController(NSObject):
    def initWithPreferences_(self, prefs):
        self = objc.super(SettingsWindowController, self).init()
        if self is None:
            return None
        self._prefs = prefs
        self._window = None
        self._permission_timer = None
        self._acc_label = None
        self._mic_label = None
        self._shortcut_field = None
        self._mic_popup = None
        self._mic_device_ids = [None]
        self._login_checkbox = None
        self._custom_words_field = None
        self._build_window()
        return self

    def _build_window(self):
        frame = NSMakeRect(0, 0, 400, 486)
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("Settings")
        self._window.setReleasedWhenClosed_(False)
        self._window.center()
        self._window.setDelegate_(self)

        content = self._window.contentView()
        y = 472

        # --- Shortcut ---
        y -= 30
        label = NSTextField.labelWithString_("Shortcut")
        label.setFrame_(NSMakeRect(20, y, 360, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        content.addSubview_(label)

        y -= 30
        self._shortcut_field = ShortcutField.alloc().initWithFrame_preferences_(
            NSMakeRect(20, y, 280, 24), self._prefs
        )
        content.addSubview_(self._shortcut_field)

        change_btn = NSButton.alloc().initWithFrame_(NSMakeRect(310, y, 80, 24))
        change_btn.setTitle_("Change")
        change_btn.setBezelStyle_(NSBezelStyleRounded)
        change_btn.setTarget_(self)
        change_btn.setAction_("changeShortcut:")
        content.addSubview_(change_btn)

        # --- Microphone ---
        y -= 40
        label = NSTextField.labelWithString_("Microphone")
        label.setFrame_(NSMakeRect(20, y, 360, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        content.addSubview_(label)

        y -= 30
        self._mic_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(20, y, 360, 24), False
        )
        self._populate_mics()
        self._mic_popup.setTarget_(self)
        self._mic_popup.setAction_("micChanged:")
        content.addSubview_(self._mic_popup)

        # --- Model ---
        y -= 40
        label = NSTextField.labelWithString_("Model")
        label.setFrame_(NSMakeRect(20, y, 360, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        content.addSubview_(label)

        y -= 26
        model_label = NSTextField.labelWithString_(self._prefs.model_id)
        model_label.setFrame_(NSMakeRect(20, y, 360, 20))
        model_label.setTextColor_(NSColor.secondaryLabelColor())
        content.addSubview_(model_label)

        # --- Custom Words ---
        y -= 40
        label = NSTextField.labelWithString_("Custom Words")
        label.setFrame_(NSMakeRect(20, y, 360, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        content.addSubview_(label)

        y -= 26
        self._custom_words_field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(20, y, 360, 24)
        )
        self._custom_words_field.setStringValue_(self._prefs.custom_words)
        self._custom_words_field.setPlaceholderString_("MLX, Qwen, vvrite")
        self._custom_words_field.setDelegate_(self)
        content.addSubview_(self._custom_words_field)

        y -= 20
        hint = NSTextField.labelWithString_(
            "인식이 잘 안 되는 단어를 쉼표로 구분해서 입력하세요"
        )
        hint.setFrame_(NSMakeRect(20, y, 360, 16))
        hint.setFont_(NSFont.systemFontOfSize_(11.0))
        hint.setTextColor_(NSColor.secondaryLabelColor())
        content.addSubview_(hint)

        # --- Permissions ---
        y -= 40
        label = NSTextField.labelWithString_("Permissions")
        label.setFrame_(NSMakeRect(20, y, 360, 20))
        label.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        content.addSubview_(label)

        y -= 26
        self._acc_label = NSTextField.labelWithString_("Accessibility: checking...")
        self._acc_label.setFrame_(NSMakeRect(20, y, 250, 20))
        content.addSubview_(self._acc_label)

        acc_btn = NSButton.alloc().initWithFrame_(NSMakeRect(310, y, 70, 24))
        acc_btn.setTitle_("Open")
        acc_btn.setBezelStyle_(NSBezelStyleRounded)
        acc_btn.setTarget_(self)
        acc_btn.setAction_("openAccessibility:")
        content.addSubview_(acc_btn)

        y -= 26
        self._mic_label = NSTextField.labelWithString_("Microphone: checking...")
        self._mic_label.setFrame_(NSMakeRect(20, y, 250, 20))
        content.addSubview_(self._mic_label)

        mic_perm_btn = NSButton.alloc().initWithFrame_(NSMakeRect(310, y, 70, 24))
        mic_perm_btn.setTitle_("Open")
        mic_perm_btn.setBezelStyle_(NSBezelStyleRounded)
        mic_perm_btn.setTarget_(self)
        mic_perm_btn.setAction_("openMicrophonePrivacy:")
        content.addSubview_(mic_perm_btn)

        # --- Launch at Login ---
        y -= 40
        self._login_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, y, 360, 20))
        self._login_checkbox.setButtonType_(NSButtonTypeSwitch)
        self._login_checkbox.setTitle_("Launch at login")
        self._login_checkbox.setState_(1 if self._prefs.launch_at_login else 0)
        self._login_checkbox.setTarget_(self)
        self._login_checkbox.setAction_("loginToggled:")
        content.addSubview_(self._login_checkbox)

        # --- Automatically check for updates ---
        y -= 34
        self._update_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, y, 360, 20))
        self._update_checkbox.setButtonType_(NSButtonTypeSwitch)
        self._update_checkbox.setTitle_("Automatically check for updates")
        self._update_checkbox.setState_(1 if self._prefs.auto_update_check else 0)
        self._update_checkbox.setTarget_(self)
        self._update_checkbox.setAction_("updateCheckToggled:")
        content.addSubview_(self._update_checkbox)

        self._update_permissions()
        self._refresh_login_checkbox()

    def _populate_mics(self):
        self._mic_popup.removeAllItems()
        devices = list_input_devices()
        default_device = get_default_input_device(devices)
        default_label = "System Default"
        if default_device is not None:
            default_label = f"System Default ({default_device.name})"
        self._mic_popup.addItemWithTitle_(default_label)

        self._mic_device_ids = [None]
        current = self._prefs.mic_device
        selected_idx = 0
        selected_device = resolve_input_device(current, devices)

        for device in devices:
            self._mic_popup.addItemWithTitle_(device.display_name)
            self._mic_device_ids.append(device.device_id)
            if selected_device is not None and selected_device.device_id == device.device_id:
                selected_idx = self._mic_popup.numberOfItems() - 1

        self._mic_popup.selectItemAtIndex_(selected_idx)

    def _update_permissions(self):
        trusted = ApplicationServices.AXIsProcessTrusted()
        self._acc_label.setStringValue_(
            f"Accessibility: {'✅ Granted' if trusted else '❌ Not Granted'}"
        )
        self._mic_label.setStringValue_("Microphone: ✅ Granted")

    def showWindow_(self, sender):
        self._populate_mics()
        self._window.makeKeyAndOrderFront_(sender)
        self._permission_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            2.0, self, "pollPermissions:", None, True
        )

    def window(self):
        return self._window

    def windowWillClose_(self, notification):
        self._save_custom_words()
        if self._permission_timer:
            self._permission_timer.invalidate()
            self._permission_timer = None

    def _save_custom_words(self):
        if self._custom_words_field is None:
            return
        self._prefs.custom_words = self._custom_words_field.stringValue()

    @objc.typedSelector(b"v@:@")
    def pollPermissions_(self, timer):
        self._update_permissions()

    @objc.typedSelector(b"v@:@")
    def changeShortcut_(self, sender):
        self._shortcut_field.startCapture()

    @objc.typedSelector(b"v@:@")
    def micChanged_(self, sender):
        index = sender.indexOfSelectedItem()
        if index <= 0:
            self._prefs.mic_device = None
        else:
            self._prefs.mic_device = self._mic_device_ids[index]

    @objc.typedSelector(b"v@:@")
    def loginToggled_(self, sender):
        enabled = sender.state() == 1
        try:
            actual_state = launch_at_login.set_enabled(enabled)
            self._prefs.launch_at_login = actual_state
        except launch_at_login.LaunchAtLoginError as e:
            NSLog(f"Launch at login toggle failed: {e}")
            self._show_launch_at_login_error(str(e))
        finally:
            self._refresh_login_checkbox()

    @objc.typedSelector(b"v@:@")
    def updateCheckToggled_(self, sender):
        self._prefs.auto_update_check = sender.state() == 1

    def controlTextDidEndEditing_(self, notification):
        field = notification.object()
        if field == self._custom_words_field:
            self._save_custom_words()

    @objc.typedSelector(b"v@:@")
    def openAccessibility_(self, sender):
        url = NSURL.URLWithString_(
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        )
        NSWorkspace.sharedWorkspace().openURL_(url)

    @objc.typedSelector(b"v@:@")
    def openMicrophonePrivacy_(self, sender):
        url = NSURL.URLWithString_(
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
        )
        NSWorkspace.sharedWorkspace().openURL_(url)

    def _refresh_login_checkbox(self):
        if self._login_checkbox is None:
            return

        support_error = launch_at_login.support_error()
        if support_error:
            self._login_checkbox.setEnabled_(False)
            self._login_checkbox.setState_(1 if self._prefs.launch_at_login else 0)
            return

        self._login_checkbox.setEnabled_(True)
        actual_state = launch_at_login.is_registered()
        self._prefs.launch_at_login = actual_state
        self._login_checkbox.setState_(1 if actual_state else 0)

    def _show_launch_at_login_error(self, message):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Launch at login could not be updated")
        alert.setInformativeText_(message)
        alert.runModal()
