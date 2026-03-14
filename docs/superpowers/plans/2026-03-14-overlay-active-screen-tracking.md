# Overlay Active Screen Tracking Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the overlay panel always appear on the user's active screen and follow them across screens during recording and transcribing.

**Architecture:** Add a `_find_active_screen()` fallback chain (frontmost app window → mouse cursor → main screen) to `OverlayController`, replace `NSScreen.mainScreen()` in `_position_panel()`, and add periodic repositioning during both recording and transcribing states.

**Tech Stack:** PyObjC (AppKit, Quartz CoreGraphics)

---

## File Structure

- Modify: `vvrite/overlay.py` — all changes are in this single file

---

## Chunk 1: Implementation

### Task 1: Add imports and instance variables

**Files:**
- Modify: `vvrite/overlay.py:1-28` (imports) and `vvrite/overlay.py:44-60` (init)

- [ ] **Step 1: Add new imports**

Add to `vvrite/overlay.py` after the existing imports:

```python
import os

from AppKit import NSWorkspace, NSEvent
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGWindowListExcludeDesktopElements,
    kCGNullWindowID,
)
```

- [ ] **Step 2: Add new instance variables in `init()`**

Add after `self._level_history = [0.0] * 8` (line 58):

```python
self._tick_count = 0
self._reposition_timer = None
```

- [ ] **Step 3: Commit**

```bash
git add vvrite/overlay.py
git commit -m "Add imports and instance variables for active screen tracking"
```

### Task 2: Implement `_find_active_screen()`

**Files:**
- Modify: `vvrite/overlay.py` — add method before `_position_panel()`

- [ ] **Step 1: Add `_find_active_screen()` method**

Insert before `_position_panel()` (before line 165):

```python
def _find_active_screen(self):
    """Return the NSScreen the user is most likely looking at.

    Fallback chain: frontmost app window → mouse cursor → main screen.
    """
    # Step 1: Try frontmost app's window position
    screen = self._screen_from_frontmost_window()
    if screen is not None:
        return screen

    # Step 2: Try mouse cursor position
    screen = self._screen_from_mouse()
    if screen is not None:
        return screen

    # Step 3: Fall back to main screen
    return NSScreen.mainScreen()

def _screen_from_frontmost_window(self):
    """Find the screen containing the frontmost app's key window."""
    frontmost = NSWorkspace.sharedWorkspace().frontmostApplication()
    if frontmost is None:
        return None

    pid = frontmost.processIdentifier()

    # Exclude vvrite's own windows (Settings, Onboarding)
    if pid == os.getpid():
        return None

    window_list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
        kCGNullWindowID,
    )
    if window_list is None:
        return None

    for win in window_list:
        if win.get("kCGWindowOwnerPID") != pid:
            continue
        if win.get("kCGWindowLayer", -1) != 0:
            continue
        bounds = win.get("kCGWindowBounds")
        if not bounds:
            continue
        w = bounds.get("Width", 0)
        h = bounds.get("Height", 0)
        if w <= 0 or h <= 0:
            continue

        # Convert Quartz coords (origin top-left) to Cocoa (origin bottom-left)
        primary = NSScreen.screens()[0].frame()
        cg_x = bounds["X"]
        cg_y = bounds["Y"]
        cocoa_x = cg_x
        cocoa_y = primary.size.height - cg_y - h

        # Find the screen containing the center of this window
        center_x = cocoa_x + w / 2
        center_y = cocoa_y + h / 2
        for s in NSScreen.screens():
            f = s.frame()
            if (f.origin.x <= center_x < f.origin.x + f.size.width
                    and f.origin.y <= center_y < f.origin.y + f.size.height):
                return s
        return None
    return None

def _screen_from_mouse(self):
    """Find the screen containing the mouse cursor."""
    mouse = NSEvent.mouseLocation()
    for s in NSScreen.screens():
        f = s.frame()
        if (f.origin.x <= mouse.x < f.origin.x + f.size.width
                and f.origin.y <= mouse.y < f.origin.y + f.size.height):
            return s
    return None
```

- [ ] **Step 2: Commit**

```bash
git add vvrite/overlay.py
git commit -m "Add _find_active_screen() with fallback chain"
```

### Task 3: Update `_position_panel()` and add periodic repositioning

**Files:**
- Modify: `vvrite/overlay.py` — `_position_panel()`, `showRecording()`, `updateDisplay_()`, `showTranscribing()`, `dismiss_()`

- [ ] **Step 1: Update `_position_panel()`**

Replace the existing `_position_panel()` method:

```python
def _position_panel(self):
    screen = self._find_active_screen()
    if screen is None:
        return
    screen_frame = screen.visibleFrame()
    panel_frame = self._panel.frame()
    x = screen_frame.origin.x + (screen_frame.size.width - panel_frame.size.width) / 2
    y = screen_frame.origin.y + 60
    self._panel.setFrameOrigin_((x, y))
```

- [ ] **Step 2: Add tick counter reset and reposition timer cleanup in `showRecording()`**

Add at the start of `showRecording()`, after `self._record_start_time = time.time()`:

```python
self._tick_count = 0
if self._reposition_timer:
    self._reposition_timer.invalidate()
    self._reposition_timer = None
```

- [ ] **Step 3: Add periodic repositioning in `updateDisplay_()`**

Add at the end of `updateDisplay_()`:

```python
# Reposition every ~0.5s (every 10 ticks at 50ms interval)
self._tick_count += 1
if self._tick_count % 10 == 0:
    self._position_panel()
```

- [ ] **Step 4: Add immediate reposition and reposition timer in `showTranscribing()`**

Add at the end of `showTranscribing()`:

```python
self._position_panel()
self._reposition_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
    1.0, self, "repositionPanel:", None, True
)
```

- [ ] **Step 5: Add `repositionPanel_` selector**

Add a new method after `updateDisplay_`:

```python
@objc.typedSelector(b"v@:@")
def repositionPanel_(self, timer):
    self._position_panel()
```

- [ ] **Step 6: Invalidate reposition timer in `dismiss_()` and `showError_()`**

Add in `dismiss_()`, after the `_update_timer` invalidation block:

```python
if self._reposition_timer:
    self._reposition_timer.invalidate()
    self._reposition_timer = None
```

Add the same block in `showError_()`, after the `_update_timer` invalidation block (line 208-210).

- [ ] **Step 7: Commit**

```bash
git add vvrite/overlay.py
git commit -m "Use active screen tracking and periodic repositioning for overlay"
```

### Task 4: Manual testing

- [ ] **Step 1: Run the app**

```bash
cd /Users/shpark/dev/vvrite && python -m vvrite
```

- [ ] **Step 2: Test multi-display** — Focus an app on a secondary monitor, trigger recording, verify overlay appears on that monitor.

- [ ] **Step 3: Test screen switching** — Start recording on one screen, switch focus to another, verify overlay follows within ~0.5 seconds.

- [ ] **Step 4: Test fullscreen** — Enter a fullscreen app, trigger recording, verify overlay is visible.

- [ ] **Step 5: Test mouse fallback** — Click desktop (no focused window), trigger recording, verify overlay appears on the screen with the mouse cursor.

- [ ] **Step 6: Test transcribing follow** — Start recording, let it transcribe, switch screens during transcribing, verify overlay follows.

- [ ] **Step 7: Test Settings self-exclusion** — Open Settings window, switch to another app on a different monitor, trigger recording, verify overlay appears on the other app's screen (not the Settings screen).

- [ ] **Step 8: Final commit**

```bash
git add vvrite/overlay.py
git commit -m "Overlay follows user's active screen across displays and fullscreen"
```
