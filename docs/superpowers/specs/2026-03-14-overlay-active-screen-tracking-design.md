# Overlay Active Screen Tracking

## Problem

The overlay panel does not always appear on the screen the user is currently looking at. This happens in two scenarios:

1. **Multi-display**: The overlay appears on a different monitor than the one with the user's focused app.
2. **Fullscreen apps**: The overlay may not be visible when the user is in a fullscreen Space.

The root cause is `_position_panel()` in `overlay.py` using `NSScreen.mainScreen()`, which does not reliably return the screen with the user's active window — especially for a menu bar app (LSUIElement) that has no key window of its own.

Additionally, `_position_panel()` is only called once at the start of recording. If the user switches screens during recording, the overlay stays on the original screen.

## Solution

Replace `NSScreen.mainScreen()` with a new `_find_active_screen()` method that uses a fallback chain to determine the correct screen. Also, periodically reposition the overlay during recording and transcribing so it follows the user across screens.

## Design

### New method: `_find_active_screen()`

Returns the `NSScreen` the user is most likely looking at, using this fallback chain:

1. **Frontmost app window** — Get the frontmost application's PID via `NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()`. Exclude vvrite's own PID (`os.getpid()`) to avoid tracking the Settings or Onboarding window instead of the user's actual app. Query `CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements, kCGNullWindowID)` for on-screen windows. Handle the case where this returns `None` (e.g., no Screen Recording permission) by falling through to the next step. Find the first window matching the PID with valid bounds (width > 0, height > 0, `kCGWindowLayer` == 0 for normal window layer). Convert Quartz screen coordinates (origin top-left) to Cocoa coordinates (origin bottom-left) using: `cocoa_y = primary_screen_height - cg_y - window_height`. Determine which `NSScreen` contains the center point of the converted bounds.
2. **Mouse cursor position** — Use `NSEvent.mouseLocation()` (returns global Cocoa coordinates) and find the `NSScreen` whose `frame()` (not `visibleFrame()`) contains that point.
3. **Main screen** — Fall back to `NSScreen.mainScreen()`.

### Modified: `_position_panel()`

Replace `NSScreen.mainScreen()` with `self._find_active_screen()`. No other changes to the positioning logic. This automatically covers both `showRecording()` and `showError_()` call sites.

### New: periodic repositioning during recording

The existing `updateDisplay_` timer fires every 50ms. Add a tick counter (`_tick_count`) and call `_position_panel()` every 10 ticks (~0.5 seconds). This avoids calling `CGWindowListCopyWindowInfo` at 20Hz while still providing responsive screen tracking.

Reset `_tick_count` to 0 in `showRecording()`.

### New: repositioning during transcribing

The `updateDisplay_` timer is invalidated when transitioning to the transcribing state, so a separate low-frequency timer (`_reposition_timer`, 1 second interval) is started in `showTranscribing()` to continue screen tracking. This timer calls `_position_panel()` and is invalidated in `dismiss_()`.

### Additional imports in `overlay.py`

- `Quartz`: `CGWindowListCopyWindowInfo`, `kCGWindowListOptionOnScreenOnly`, `kCGWindowListExcludeDesktopElements`, `kCGNullWindowID`
- `AppKit`: `NSWorkspace`, `NSEvent`
- `os` (for `os.getpid()`)

## Files changed

- `vvrite/overlay.py` — all changes are in this single file

## Testing

- Manual: connect external display, trigger recording, verify overlay appears on the monitor with the focused app.
- Manual: start recording on one screen, switch focus to another screen, verify overlay follows within ~0.5 seconds.
- Manual: enter fullscreen app, trigger recording, verify overlay is visible.
- Manual: trigger recording with no focused window (e.g., click desktop), verify overlay falls back to mouse cursor screen.
- Manual: start recording, then switch screens during transcribing phase, verify overlay follows.
- Manual: open Settings window, trigger recording from another app, verify overlay appears on the other app's screen (not the Settings screen).
