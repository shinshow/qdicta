# Whisper Backends Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Whisper large-v3 and Whisper large-v3-turbo as selectable local/free ASR models alongside the existing Qwen3-ASR model, while preserving menu-bar responsiveness and adding an English translation output mode where supported.

**Architecture:** Keep Qwen3-ASR on the existing in-process `mlx-audio` path. Add Whisper through a `whisper.cpp` sidecar executable so Whisper runs only during transcription and releases memory when the process exits. Introduce a small model registry that drives settings UI, download/cached checks, backend routing, and feature availability so only the selected model is active.

**Tech Stack:** Python, PyObjC/AppKit, NSUserDefaults, mlx-audio, Hugging Face Hub, whisper.cpp, PyInstaller, macOS codesign/notarytool, `unittest`

---

## Current Context

- Current default model is `mlx-community/Qwen3-ASR-1.7B-8bit` in `vvrite/preferences.py`.
- Current transcriber is Qwen-specific: `vvrite/transcriber.py` imports `mlx_audio.stt.utils.load_model` and calls `_model.generate(...)`.
- Current settings UI only displays the model ID as a label in `vvrite/settings.py`; it does not let users switch models.
- Current onboarding downloads/loads `prefs.model_id` through `vvrite/onboarding.py`.
- Current Qwen downloads use Hugging Face Hub's default cache. On this machine, the existing Qwen cache was observed at `~/.cache/huggingface/hub/models--mlx-community--Qwen3-ASR-1.7B-8bit` with about `2.3G` used.
- Current build path is `./scripts/build.sh`; do not run `pyinstaller vvrite.spec` directly.
- Existing untracked files at plan creation time: `docs/superpowers/plans/2026-04-25-v1-0-6-sync.md`, `firebase-debug.log`. Do not include these in feature commits unless explicitly requested.

## Product Decisions

- Keep `Qwen3-ASR` as the default model for compatibility and fast existing behavior.
- Add `Whisper large-v3` for accuracy and Korean-to-English translation.
- Add `Whisper large-v3-turbo` for faster multilingual transcription.
- Support two output modes:
  - `transcribe`: preserve the spoken language, including Korean/English code-switching.
  - `translate_to_english`: translate spoken Korean/multilingual speech to English text.
- Enable `translate_to_english` only for `Whisper large-v3` in the first implementation. `Whisper large-v3-turbo` is treated as transcription-only because public API documentation commonly marks turbo translation as unsupported; do not promise translation for turbo without local validation.
- Use only free/local models. Do not add Groq, OpenAI API, DashScope, or any paid cloud dependency.
- Load or execute only the selected model. Never load all three models at app startup.
- Store all app-managed models under `~/Library/Application Support/vvrite/models/`. Do not continue adding new downloads to the global Hugging Face cache.
- Do not auto-delete existing Hugging Face cache content. The current Qwen cache may already exist at `~/.cache/huggingface/hub/models--mlx-community--Qwen3-ASR-1.7B-8bit`; leave it alone unless the user explicitly chooses a cleanup action.
- Settings must expose model deletion per downloaded model so users can reclaim disk space without manually finding cache folders.
- Document that deleting `/Applications/vvrite.app` does not automatically delete models stored in `~/Library/Application Support/vvrite/models/`.

## Performance Requirements

- Menu-bar idle state must not keep Whisper models in memory.
- Whisper must run as a subprocess via `whisper.cpp` and exit after each transcription.
- Qwen may remain in-process as it does today, but switching away from Qwen must release `_model` and reset warm-up state.
- Model downloads must run on background threads and must not block AppKit.
- Model switch must not trigger synchronous model load on the main thread.
- Model deletion must unload the currently loaded model before deleting its app-managed model directory.
- The UI must clearly show that installing all models requires roughly 7 GB of disk space:
  - Qwen3-ASR 8-bit MLX: about 2.5 GB.
  - Whisper large-v3 GGML: about 2.9 GiB.
  - Whisper large-v3-turbo GGML: about 1.5 GiB.

## Better Process Recommendation

This checklist file is enough for a new session to continue implementation. A better long-term process is to also create a short design/spec document in `docs/superpowers/specs/2026-04-25-whisper-backends-design.md` before implementation, then commit the spec separately. That gives future contributors a stable rationale document while this plan remains the execution checklist.

## File Map

- Create: `vvrite/asr_models.py`
  - Owns model keys, backend keys, output modes, download URLs, feature flags, and display labels.
- Create: `vvrite/model_store.py`
  - Owns app-specific model storage paths, directory creation, size calculation, and safe deletion under `~/Library/Application Support/vvrite/models/`.
- Create: `vvrite/asr_backends/__init__.py`
  - Package marker and shared backend exports.
- Create: `vvrite/asr_backends/qwen.py`
  - Moves existing Qwen-specific load/download/transcribe behavior out of `transcriber.py`.
- Create: `vvrite/asr_backends/whisper_cpp.py`
  - Owns whisper.cpp binary path lookup, model file download, cached checks, subprocess invocation, and text cleanup.
- Modify: `vvrite/transcriber.py`
  - Becomes a router that preserves the existing public functions: `is_model_loaded`, `is_model_cached`, `get_model_size`, `download_model`, `load_from_local`, `load`, `transcribe`, and adds `delete_model`.
- Modify: `vvrite/preferences.py`
  - Adds `asr_model_key` and `output_mode`, keeps `model_id` as compatibility accessor for Qwen-era settings.
- Modify: `vvrite/settings.py`
  - Replaces model label with model popup, adds output mode popup, adds download/status/delete controls for selected model.
- Modify: `vvrite/onboarding.py`
  - Keeps first-run default Qwen download in v1, but uses model registry and router APIs so future onboarding model choice is straightforward.
- Modify: `vvrite/main.py`
  - Checks selected model cache instead of raw `prefs.model_id`; ensures model switching does not block UI.
- Modify: `vvrite/locales/*.py`
  - Adds localized labels for model selection, output mode, unsupported translation, download status, and model deletion.
- Modify: `vvrite.spec`
  - Bundles whisper.cpp sidecar executable.
- Modify: `scripts/build.sh`
  - Builds/verifies whisper.cpp sidecar before PyInstaller and signs arbitrary embedded executables, not only `.so`, `.dylib`, frameworks, and main binary.
- Create: `scripts/build_whisper_cpp.sh`
  - Builds a pinned whisper.cpp CLI binary for Apple Silicon.
- Modify: `README*.md`
  - Documents selectable ASR models, translation mode limitations, disk usage, and local-only privacy behavior.
- Test: `tests/test_asr_models.py`
- Test: `tests/test_model_store.py`
- Test: `tests/test_preferences.py`
- Test: `tests/test_transcriber.py`
- Test: `tests/test_whisper_cpp_backend.py`
- Test: `tests/test_settings.py`
- Test: `tests/test_locales.py`

---

### Task 1: Preflight And Baseline

**Files:**
- Read: `AGENTS.md`
- Read: `vvrite/preferences.py`
- Read: `vvrite/transcriber.py`
- Read: `vvrite/settings.py`
- Read: `vvrite/onboarding.py`
- Read: `scripts/build.sh`
- Read: `vvrite.spec`

- [ ] **Step 1: Confirm clean scope**

Run:

```bash
git status --short --branch
```

Expected: only known unrelated untracked files may be present, currently:

```text
?? docs/superpowers/plans/2026-04-25-v1-0-6-sync.md
?? firebase-debug.log
```

If additional modified tracked files exist, inspect them before editing and do not overwrite user work.

- [ ] **Step 2: Run focused baseline tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_preferences tests.test_transcriber tests.test_settings tests.test_locales
```

Expected: all non-MLX tests pass. If `tests.test_transcriber` fails with `No Metal device available`, document it and use narrower mocked tests for transcriber changes.

- [ ] **Step 3: Commit nothing**

This task only establishes the baseline. Do not commit unless you had to add a test environment note requested by the user.

---

### Task 2: Add Model Registry

**Files:**
- Create: `vvrite/asr_models.py`
- Create: `tests/test_asr_models.py`

- [ ] **Step 1: Write registry tests**

Create `tests/test_asr_models.py` with:

```python
"""Tests for ASR model registry."""

import unittest

from vvrite.asr_models import (
    ASR_MODELS,
    DEFAULT_ASR_MODEL_KEY,
    OUTPUT_MODE_TRANSCRIBE,
    OUTPUT_MODE_TRANSLATE_TO_ENGLISH,
    get_model,
    is_output_mode_supported,
)


class TestAsrModels(unittest.TestCase):
    def test_default_model_is_qwen(self):
        self.assertEqual(DEFAULT_ASR_MODEL_KEY, "qwen3_asr_1_7b_8bit")
        self.assertEqual(get_model(DEFAULT_ASR_MODEL_KEY).backend, "qwen_mlx")

    def test_contains_three_selectable_models(self):
        self.assertEqual(
            set(ASR_MODELS),
            {
                "qwen3_asr_1_7b_8bit",
                "whisper_large_v3",
                "whisper_large_v3_turbo",
            },
        )

    def test_whisper_large_v3_supports_translation(self):
        self.assertTrue(
            is_output_mode_supported(
                "whisper_large_v3", OUTPUT_MODE_TRANSLATE_TO_ENGLISH
            )
        )

    def test_qwen_and_turbo_do_not_support_translation_mode(self):
        self.assertFalse(
            is_output_mode_supported(
                "qwen3_asr_1_7b_8bit", OUTPUT_MODE_TRANSLATE_TO_ENGLISH
            )
        )
        self.assertFalse(
            is_output_mode_supported(
                "whisper_large_v3_turbo", OUTPUT_MODE_TRANSLATE_TO_ENGLISH
            )
        )

    def test_all_models_support_transcription(self):
        for key in ASR_MODELS:
            self.assertTrue(is_output_mode_supported(key, OUTPUT_MODE_TRANSCRIBE))

    def test_unknown_model_falls_back_to_default(self):
        self.assertEqual(get_model("missing").key, DEFAULT_ASR_MODEL_KEY)
```

- [ ] **Step 2: Run failing test**

Run:

```bash
.venv/bin/python -m unittest tests.test_asr_models
```

Expected: FAIL with `ModuleNotFoundError: No module named 'vvrite.asr_models'`.

- [ ] **Step 3: Add `vvrite/asr_models.py`**

Create:

```python
"""ASR model registry and feature flags."""

from dataclasses import dataclass

OUTPUT_MODE_TRANSCRIBE = "transcribe"
OUTPUT_MODE_TRANSLATE_TO_ENGLISH = "translate_to_english"

BACKEND_QWEN_MLX = "qwen_mlx"
BACKEND_WHISPER_CPP = "whisper_cpp"

DEFAULT_ASR_MODEL_KEY = "qwen3_asr_1_7b_8bit"


@dataclass(frozen=True)
class AsrModel:
    key: str
    display_name: str
    backend: str
    model_id: str
    download_url: str | None
    local_filename: str | None
    size_hint: str
    supports_language_hint: bool
    supports_translation_to_english: bool


ASR_MODELS = {
    "qwen3_asr_1_7b_8bit": AsrModel(
        key="qwen3_asr_1_7b_8bit",
        display_name="Qwen3-ASR 1.7B 8-bit",
        backend=BACKEND_QWEN_MLX,
        model_id="mlx-community/Qwen3-ASR-1.7B-8bit",
        download_url=None,
        local_filename=None,
        size_hint="~2.5 GB",
        supports_language_hint=True,
        supports_translation_to_english=False,
    ),
    "whisper_large_v3": AsrModel(
        key="whisper_large_v3",
        display_name="Whisper large-v3",
        backend=BACKEND_WHISPER_CPP,
        model_id="ggerganov/whisper.cpp/ggml-large-v3.bin",
        download_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
        local_filename="ggml-large-v3.bin",
        size_hint="~2.9 GiB",
        supports_language_hint=True,
        supports_translation_to_english=True,
    ),
    "whisper_large_v3_turbo": AsrModel(
        key="whisper_large_v3_turbo",
        display_name="Whisper large-v3-turbo",
        backend=BACKEND_WHISPER_CPP,
        model_id="ggerganov/whisper.cpp/ggml-large-v3-turbo.bin",
        download_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin",
        local_filename="ggml-large-v3-turbo.bin",
        size_hint="~1.5 GiB",
        supports_language_hint=True,
        supports_translation_to_english=False,
    ),
}


def get_model(key: str | None) -> AsrModel:
    return ASR_MODELS.get(key or "", ASR_MODELS[DEFAULT_ASR_MODEL_KEY])


def is_output_mode_supported(model_key: str, output_mode: str) -> bool:
    model = get_model(model_key)
    if output_mode == OUTPUT_MODE_TRANSCRIBE:
        return True
    if output_mode == OUTPUT_MODE_TRANSLATE_TO_ENGLISH:
        return model.supports_translation_to_english
    return False
```

- [ ] **Step 4: Run test**

Run:

```bash
.venv/bin/python -m unittest tests.test_asr_models
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add vvrite/asr_models.py tests/test_asr_models.py
git commit -m "feat: add ASR model registry"
```

---

### Task 3: Add Preferences For Model Key And Output Mode

**Files:**
- Modify: `vvrite/preferences.py`
- Modify: `tests/test_preferences.py`

- [ ] **Step 1: Add failing preference tests**

Append tests inside `TestPreferences` in `tests/test_preferences.py`:

```python
    def test_default_asr_model_key(self):
        prefs = Preferences()
        self.assertEqual(prefs.asr_model_key, "qwen3_asr_1_7b_8bit")

    def test_default_output_mode(self):
        prefs = Preferences()
        self.assertEqual(prefs.output_mode, "transcribe")

    def test_set_asr_model_key(self):
        prefs = Preferences()
        prefs.asr_model_key = "whisper_large_v3"
        self.assertEqual(prefs.asr_model_key, "whisper_large_v3")

    def test_set_output_mode(self):
        prefs = Preferences()
        prefs.output_mode = "translate_to_english"
        self.assertEqual(prefs.output_mode, "translate_to_english")

    def test_model_id_compatibility_tracks_selected_model(self):
        prefs = Preferences()
        prefs.asr_model_key = "whisper_large_v3"
        self.assertEqual(prefs.model_id, "ggerganov/whisper.cpp/ggml-large-v3.bin")
```

Also add `"asr_model_key"` and `"output_mode"` to `_TEST_KEYS`.

- [ ] **Step 2: Run failing tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_preferences
```

Expected: FAIL because the new properties do not exist.

- [ ] **Step 3: Update preferences defaults and accessors**

In `vvrite/preferences.py`, import registry constants:

```python
from vvrite.asr_models import (
    DEFAULT_ASR_MODEL_KEY,
    OUTPUT_MODE_TRANSCRIBE,
    get_model,
)
```

Update `_DEFAULTS`:

```python
    "model_id": "mlx-community/Qwen3-ASR-1.7B-8bit",
    "asr_model_key": DEFAULT_ASR_MODEL_KEY,
    "output_mode": OUTPUT_MODE_TRANSCRIBE,
```

Replace `model_id` property with compatibility behavior:

```python
    @property
    def model_id(self) -> str:
        return get_model(self.asr_model_key).model_id

    @model_id.setter
    def model_id(self, value: str):
        self._set("model_id", value)
        if value == "mlx-community/Qwen3-ASR-1.7B-8bit":
            self._set("asr_model_key", DEFAULT_ASR_MODEL_KEY)
```

Add properties near `model_id`:

```python
    @property
    def asr_model_key(self) -> str:
        return str(self._get("asr_model_key"))

    @asr_model_key.setter
    def asr_model_key(self, value: str):
        self._set("asr_model_key", value)

    @property
    def output_mode(self) -> str:
        return str(self._get("output_mode"))

    @output_mode.setter
    def output_mode(self, value: str):
        self._set("output_mode", value)
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_preferences tests.test_asr_models
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add vvrite/preferences.py tests/test_preferences.py
git commit -m "feat: add ASR model preferences"
```

---

### Task 4: Add App-Specific Model Store

**Files:**
- Create: `vvrite/model_store.py`
- Create: `tests/test_model_store.py`

- [ ] **Step 1: Write model store tests**

Create `tests/test_model_store.py`:

```python
"""Tests for app-managed model storage."""

import os
import tempfile
import unittest
from unittest.mock import patch

from vvrite import model_store


class TestModelStore(unittest.TestCase):
    def test_model_root_is_under_application_support(self):
        with patch.object(
            model_store,
            "_application_support_dir",
            return_value="/Users/test/Library/Application Support/vvrite",
        ):
            self.assertEqual(
                model_store.model_root(),
                "/Users/test/Library/Application Support/vvrite/models",
            )

    def test_model_dir_uses_model_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(model_store, "model_root", return_value=tmp):
                path = model_store.model_dir("whisper_large_v3")
                self.assertEqual(path, os.path.join(tmp, "whisper_large_v3"))
                self.assertTrue(os.path.isdir(path))

    def test_model_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(model_store, "model_root", return_value=tmp):
                self.assertEqual(
                    model_store.model_file_path("whisper_large_v3", "ggml-large-v3.bin"),
                    os.path.join(tmp, "whisper_large_v3", "ggml-large-v3.bin"),
                )

    def test_delete_model_dir_removes_only_requested_model_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(model_store, "model_root", return_value=tmp):
                target = model_store.model_dir("whisper_large_v3")
                keep = model_store.model_dir("qwen3_asr_1_7b_8bit")
                open(os.path.join(target, "model.bin"), "wb").close()
                open(os.path.join(keep, "model.bin"), "wb").close()
                model_store.delete_model_dir("whisper_large_v3")
                self.assertFalse(os.path.exists(target))
                self.assertTrue(os.path.exists(keep))
```

- [ ] **Step 2: Run failing test**

Run:

```bash
.venv/bin/python -m unittest tests.test_model_store
```

Expected: FAIL because `vvrite.model_store` does not exist.

- [ ] **Step 3: Implement model store**

Create `vvrite/model_store.py`:

```python
"""App-specific model storage utilities."""

from __future__ import annotations

import os
import shutil


def _application_support_dir() -> str:
    return os.path.expanduser("~/Library/Application Support/vvrite")


def model_root() -> str:
    return os.path.join(_application_support_dir(), "models")


def model_dir(model_key: str) -> str:
    path = os.path.join(model_root(), model_key)
    os.makedirs(path, exist_ok=True)
    return path


def model_file_path(model_key: str, filename: str) -> str:
    return os.path.join(model_dir(model_key), filename)


def dir_size_bytes(path: str) -> int:
    total = 0
    if not os.path.exists(path):
        return 0
    for root, _, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                total += os.path.getsize(file_path)
            except OSError:
                pass
    return total


def delete_model_dir(model_key: str):
    root = os.path.abspath(model_root())
    target = os.path.abspath(os.path.join(root, model_key))
    if not target.startswith(root + os.sep):
        raise ValueError(f"Refusing to delete outside model root: {target}")
    shutil.rmtree(target, ignore_errors=True)
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_model_store
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add vvrite/model_store.py tests/test_model_store.py
git commit -m "feat: add app model store"
```

---

### Task 5: Split Qwen Backend From Router

**Files:**
- Create: `vvrite/asr_backends/__init__.py`
- Create: `vvrite/asr_backends/qwen.py`
- Modify: `vvrite/transcriber.py`
- Modify: `tests/test_transcriber.py`

- [ ] **Step 1: Add package marker**

Create `vvrite/asr_backends/__init__.py`:

```python
"""ASR backend implementations."""
```

- [ ] **Step 2: Move Qwen implementation**

Create `vvrite/asr_backends/qwen.py` with the current Qwen-specific functions from `vvrite/transcriber.py`:

```python
"""Qwen3-ASR backend using mlx-audio."""

import os
import tempfile

import numpy as np
import soundfile as sf
from huggingface_hub import model_info, snapshot_download
from mlx_audio.stt.utils import load_model

from vvrite import audio_utils
from vvrite.locales import ASR_LANGUAGE_MAP
from vvrite import model_store
from vvrite.preferences import SAMPLE_RATE

_model = None
_warmed_up = False


def is_loaded() -> bool:
    return _model is not None


def unload():
    global _model, _warmed_up
    _model = None
    _warmed_up = False


def is_cached(model_id: str) -> bool:
    local_dir = model_store.model_dir("qwen3_asr_1_7b_8bit")
    try:
        snapshot_download(repo_id=model_id, local_dir=local_dir, local_files_only=True)
        return True
    except Exception:
        return False


def get_size(model_id: str) -> int:
    try:
        info = model_info(model_id, files_metadata=True)
        return sum(s.size for s in info.siblings if s.size)
    except Exception:
        return 0


def download(model_id: str) -> str:
    local_dir = model_store.model_dir("qwen3_asr_1_7b_8bit")
    return snapshot_download(repo_id=model_id, local_dir=local_dir)


def load_from_local(local_path: str):
    global _model, _warmed_up
    _model = load_model(local_path)
    _warmed_up = False
    safe_warm_up()


def load(model_id: str):
    global _model, _warmed_up
    _model = load_model(model_id)
    _warmed_up = False
    safe_warm_up()


def _create_warmup_audio() -> str:
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(path, np.zeros(SAMPLE_RATE // 2, dtype=np.float32), SAMPLE_RATE)
    return path


def warm_up():
    global _warmed_up
    if _model is None or _warmed_up:
        return

    warmup_path = _create_warmup_audio()
    try:
        _model.generate(warmup_path, max_tokens=1)
        _warmed_up = True
    finally:
        try:
            os.unlink(warmup_path)
        except OSError:
            pass


def safe_warm_up():
    try:
        warm_up()
    except Exception as e:
        print(f"Model warm-up skipped: {e}")


def transcribe(raw_wav_path: str, prefs) -> str:
    if _model is None:
        raise RuntimeError("Qwen3-ASR model is not loaded")

    normalized_path = audio_utils.normalize(raw_wav_path)
    try:
        kwargs = {"max_tokens": prefs.max_tokens}
        custom_words = prefs.custom_words.strip()
        if custom_words:
            kwargs["system_prompt"] = f"Use the following spellings: {custom_words}"

        asr_lang = prefs.asr_language
        if asr_lang != "auto":
            language_param = ASR_LANGUAGE_MAP.get(asr_lang)
            if language_param is None:
                print(f"Unknown ASR language code: {asr_lang}, falling back to auto-detect")
            else:
                kwargs["language"] = language_param

        result = _model.generate(normalized_path, **kwargs)
        return result.text.strip()
    finally:
        for path in (raw_wav_path, normalized_path):
            try:
                os.unlink(path)
            except OSError:
                pass
```

- [ ] **Step 3: Replace `vvrite/transcriber.py` with router preserving public API**

Use this structure:

```python
"""ASR transcription router."""

from vvrite.asr_models import BACKEND_QWEN_MLX, get_model
from vvrite.asr_backends import qwen
from vvrite.preferences import Preferences

_loaded_model_key = None


def _selected_model(prefs: Preferences | None = None):
    if prefs is None:
        prefs = Preferences()
    return get_model(prefs.asr_model_key)


def is_model_loaded() -> bool:
    return _loaded_model_key is not None and qwen.is_loaded()


def is_model_cached(model_id_or_key: str) -> bool:
    model = get_model(model_id_or_key)
    if model.backend == BACKEND_QWEN_MLX:
        return qwen.is_cached(model.model_id)
    raise RuntimeError(f"Unsupported backend before Whisper task: {model.backend}")


def get_model_size(model_id_or_key: str) -> int:
    model = get_model(model_id_or_key)
    if model.backend == BACKEND_QWEN_MLX:
        return qwen.get_size(model.model_id)
    return 0


def download_model(model_id_or_key: str) -> str:
    model = get_model(model_id_or_key)
    if model.backend == BACKEND_QWEN_MLX:
        return qwen.download(model.model_id)
    raise RuntimeError(f"Unsupported backend before Whisper task: {model.backend}")


def load_from_local(local_path: str, prefs: Preferences = None):
    global _loaded_model_key
    model = _selected_model(prefs)
    if model.backend == BACKEND_QWEN_MLX:
        qwen.load_from_local(local_path)
        _loaded_model_key = model.key
        return
    raise RuntimeError(f"Unsupported backend before Whisper task: {model.backend}")


def load(prefs: Preferences = None):
    global _loaded_model_key
    if prefs is None:
        prefs = Preferences()
    model = _selected_model(prefs)
    print(f"Loading model: {model.display_name} ({model.model_id}) ...")
    if model.backend == BACKEND_QWEN_MLX:
        qwen.load(model.model_id)
        _loaded_model_key = model.key
        print("Model loaded.")
        return
    raise RuntimeError(f"Unsupported backend before Whisper task: {model.backend}")


def unload():
    global _loaded_model_key
    qwen.unload()
    _loaded_model_key = None


def delete_model(model_key: str):
    from vvrite import model_store
    unload()
    model_store.delete_model_dir(get_model(model_key).key)


def transcribe(raw_wav_path: str, prefs: Preferences = None) -> str:
    if prefs is None:
        prefs = Preferences()
    model = _selected_model(prefs)
    if model.backend == BACKEND_QWEN_MLX:
        return qwen.transcribe(raw_wav_path, prefs)
    raise RuntimeError(f"Unsupported backend before Whisper task: {model.backend}")
```

- [ ] **Step 4: Update tests for moved mocks**

In `tests/test_transcriber.py`, patch router-level or backend-level symbols consistently:

```python
@patch("vvrite.asr_backends.qwen.model_info")
@patch("vvrite.asr_backends.qwen.snapshot_download")
@patch("vvrite.asr_backends.qwen.load_model")
```

Keep assertions equivalent to existing Qwen behavior.

- [ ] **Step 5: Run tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_transcriber tests.test_preferences tests.test_asr_models
```

Expected: PASS or only documented `No Metal device available` failures if real MLX import is unavoidable. If MLX import causes failures, defer importing `vvrite.asr_backends.qwen` in `transcriber.py` until a Qwen function is called.

- [ ] **Step 6: Commit**

Run:

```bash
git add vvrite/transcriber.py vvrite/asr_backends/__init__.py vvrite/asr_backends/qwen.py tests/test_transcriber.py
git commit -m "refactor: split Qwen ASR backend"
```

---

### Task 6: Add Whisper.cpp Backend

**Files:**
- Create: `vvrite/asr_backends/whisper_cpp.py`
- Modify: `vvrite/transcriber.py`
- Create: `tests/test_whisper_cpp_backend.py`
- Modify: `tests/test_transcriber.py`

- [ ] **Step 1: Write Whisper backend tests**

Create `tests/test_whisper_cpp_backend.py`:

```python
"""Tests for whisper.cpp backend."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from vvrite.asr_models import OUTPUT_MODE_TRANSCRIBE, OUTPUT_MODE_TRANSLATE_TO_ENGLISH
from vvrite.asr_backends import whisper_cpp


class _Prefs:
    asr_language = "ko"
    output_mode = OUTPUT_MODE_TRANSCRIBE
    custom_words = "MLX, vvrite"


class TestWhisperCppBackend(unittest.TestCase):
    def test_model_cache_path_uses_local_filename(self):
        model = MagicMock(key="whisper_large_v3", local_filename="ggml-large-v3.bin")
        with patch("vvrite.model_store.model_root", return_value="/tmp/models"):
            self.assertEqual(
                whisper_cpp.model_path(model),
                "/tmp/models/whisper_large_v3/ggml-large-v3.bin",
            )

    def test_is_cached_requires_file(self):
        model = MagicMock(key="whisper_large_v3", local_filename="ggml-large-v3.bin")
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vvrite.model_store.model_root", return_value=tmp):
                self.assertFalse(whisper_cpp.is_cached(model))
                os.makedirs(os.path.join(tmp, "whisper_large_v3"), exist_ok=True)
                open(
                    os.path.join(tmp, "whisper_large_v3", "ggml-large-v3.bin"),
                    "wb",
                ).close()
                self.assertTrue(whisper_cpp.is_cached(model))

    @patch("vvrite.asr_backends.whisper_cpp.subprocess.run")
    @patch("vvrite.asr_backends.whisper_cpp.binary_path", return_value="/app/whisper-cli")
    @patch("vvrite.asr_backends.whisper_cpp.model_path", return_value="/models/ggml-large-v3.bin")
    @patch("vvrite.audio_utils.normalize", return_value="/tmp/normalized.wav")
    def test_transcribe_invokes_whisper_cpp_with_language(
        self, mock_normalize, mock_model_path, mock_binary_path, mock_run
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout=" 안녕하세요 MLX", stderr="")
        model = MagicMock()
        result = whisper_cpp.transcribe("/tmp/raw.wav", model, _Prefs())
        self.assertEqual(result, "안녕하세요 MLX")
        args = mock_run.call_args.args[0]
        self.assertIn("-l", args)
        self.assertIn("ko", args)
        self.assertNotIn("--translate", args)

    @patch("vvrite.asr_backends.whisper_cpp.subprocess.run")
    @patch("vvrite.asr_backends.whisper_cpp.binary_path", return_value="/app/whisper-cli")
    @patch("vvrite.asr_backends.whisper_cpp.model_path", return_value="/models/ggml-large-v3.bin")
    @patch("vvrite.audio_utils.normalize", return_value="/tmp/normalized.wav")
    def test_translate_mode_adds_translate_flag(
        self, mock_normalize, mock_model_path, mock_binary_path, mock_run
    ):
        prefs = _Prefs()
        prefs.output_mode = OUTPUT_MODE_TRANSLATE_TO_ENGLISH
        prefs.asr_language = "auto"
        mock_run.return_value = MagicMock(returncode=0, stdout="Hello", stderr="")
        whisper_cpp.transcribe("/tmp/raw.wav", MagicMock(), prefs)
        self.assertIn("--translate", mock_run.call_args.args[0])
```

- [ ] **Step 2: Run failing test**

Run:

```bash
.venv/bin/python -m unittest tests.test_whisper_cpp_backend
```

Expected: FAIL because `vvrite.asr_backends.whisper_cpp` does not exist.

- [ ] **Step 3: Implement Whisper backend**

Create `vvrite/asr_backends/whisper_cpp.py`:

```python
"""Whisper backend using a bundled whisper.cpp sidecar."""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request

from vvrite import audio_utils
from vvrite.asr_models import OUTPUT_MODE_TRANSLATE_TO_ENGLISH
from vvrite import model_store


def model_path(model) -> str:
    return model_store.model_file_path(model.key, model.local_filename)


def binary_path() -> str:
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(sys._MEIPASS, "whisper.cpp", "whisper-cli"))
    candidates.append(os.path.join(os.getcwd(), "vendor", "whisper.cpp", "whisper-cli"))
    candidates.append(os.path.join(os.getcwd(), "vendor", "whisper.cpp", "main"))
    for candidate in candidates:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError("whisper.cpp sidecar not found")


def is_loaded() -> bool:
    return True


def unload():
    return None


def is_cached(model) -> bool:
    return os.path.exists(model_path(model))


def get_size(model) -> int:
    try:
        request = urllib.request.Request(model.download_url, method="HEAD")
        with urllib.request.urlopen(request, timeout=20) as response:
            return int(response.headers.get("Content-Length", "0"))
    except Exception:
        return 0


def download(model) -> str:
    dest = model_path(model)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = f"{dest}.download"
    urllib.request.urlretrieve(model.download_url, tmp)
    os.replace(tmp, dest)
    return dest


def _language_arg(prefs) -> str:
    if prefs.output_mode == OUTPUT_MODE_TRANSLATE_TO_ENGLISH:
        return "auto"
    if prefs.asr_language == "auto":
        return "auto"
    return str(prefs.asr_language)


def _clean_output(stdout: str) -> str:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return "\n".join(lines).strip()


def transcribe(raw_wav_path: str, model, prefs) -> str:
    normalized_path = audio_utils.normalize(raw_wav_path)
    try:
        args = [
            binary_path(),
            "-m",
            model_path(model),
            "-f",
            normalized_path,
            "--no-timestamps",
            "-l",
            _language_arg(prefs),
        ]
        if prefs.output_mode == OUTPUT_MODE_TRANSLATE_TO_ENGLISH:
            args.append("--translate")
        custom_words = prefs.custom_words.strip()
        if custom_words:
            args.extend(["--prompt", f"Use these spellings when relevant: {custom_words}"])

        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "whisper.cpp failed")
        return _clean_output(completed.stdout)
    finally:
        for path in (raw_wav_path, normalized_path):
            try:
                os.unlink(path)
            except OSError:
                pass
```

- [ ] **Step 4: Route Whisper in `vvrite/transcriber.py`**

Update `transcriber.py` imports:

```python
from vvrite.asr_models import BACKEND_QWEN_MLX, BACKEND_WHISPER_CPP, get_model, is_output_mode_supported
from vvrite.asr_backends import qwen, whisper_cpp
```

Add validation helper:

```python
def _ensure_output_mode_supported(model, prefs):
    if not is_output_mode_supported(model.key, prefs.output_mode):
        raise RuntimeError(
            f"{model.display_name} does not support output mode {prefs.output_mode}"
        )
```

Update each router function:

```python
def is_model_cached(model_id_or_key: str) -> bool:
    model = get_model(model_id_or_key)
    if model.backend == BACKEND_QWEN_MLX:
        return qwen.is_cached(model.model_id)
    if model.backend == BACKEND_WHISPER_CPP:
        return whisper_cpp.is_cached(model)
    raise RuntimeError(f"Unsupported backend: {model.backend}")
```

Apply the same `BACKEND_WHISPER_CPP` branch to `get_model_size`, `download_model`, `load`, `load_from_local`, `unload`, `delete_model`, and `transcribe`. For Whisper `load` should only verify binary/model availability and set `_loaded_model_key`; it must not spawn a persistent model process. `delete_model(model_key)` should always call `unload()` first, then delete only `~/Library/Application Support/vvrite/models/<model_key>` through `model_store.delete_model_dir`.

- [ ] **Step 5: Run tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_whisper_cpp_backend tests.test_transcriber tests.test_asr_models
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add vvrite/asr_backends/whisper_cpp.py vvrite/transcriber.py tests/test_whisper_cpp_backend.py tests/test_transcriber.py
git commit -m "feat: add whisper.cpp ASR backend"
```

---

### Task 7: Add Settings UI For Model, Output Mode, And Model Deletion

**Files:**
- Modify: `vvrite/settings.py`
- Modify: `vvrite/locales/en.py`
- Modify: all other `vvrite/locales/*.py`
- Modify: `tests/test_settings.py`
- Modify: `tests/test_locales.py`

- [ ] **Step 1: Add locale keys**

Add these keys under `settings.model` in every locale file. English source:

```python
"model": {
    "title": "Model",
    "selected_model": "ASR model",
    "output_mode": "Output",
    "download": "Download selected model",
    "delete": "Delete selected model",
    "delete_confirm_title": "Delete downloaded model?",
    "delete_confirm_message": "This removes the selected model from vvrite's Application Support folder. You can download it again later.",
    "downloaded": "Downloaded",
    "not_downloaded": "Not downloaded",
    "delete_current_model_blocked": "Quit vvrite or switch models before deleting the currently loaded model.",
    "translation_unsupported": "English translation requires Whisper large-v3.",
    "mode_transcribe": "Transcribe in spoken language",
    "mode_translate_to_english": "Translate to English",
},
```

For non-English locale files, use clear translations and keep model names unchanged.

- [ ] **Step 2: Add locale completeness test**

In `tests/test_locales.py`, extend the settings model key assertions:

```python
for key in [
    "title",
    "selected_model",
    "output_mode",
    "download",
    "delete",
    "delete_confirm_title",
    "delete_confirm_message",
    "downloaded",
    "not_downloaded",
    "delete_current_model_blocked",
    "translation_unsupported",
    "mode_transcribe",
    "mode_translate_to_english",
]:
    self.assertIn(key, s["model"], f"Missing settings.model.{key}")
```

- [ ] **Step 3: Replace static model label in settings**

In `vvrite/settings.py`, import:

```python
from vvrite.asr_models import (
    ASR_MODELS,
    OUTPUT_MODE_TRANSCRIBE,
    OUTPUT_MODE_TRANSLATE_TO_ENGLISH,
    get_model,
    is_output_mode_supported,
)
from vvrite import transcriber
```

Replace the current model label block with:

```python
self._model_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
    NSMakeRect(156, y, 224, 24), False
)
for model in ASR_MODELS.values():
    self._model_popup.addItemWithTitle_(model.display_name)
current_model = get_model(self._prefs.asr_model_key)
for i, model in enumerate(ASR_MODELS.values()):
    if model.key == current_model.key:
        self._model_popup.selectItemAtIndex_(i)
        break
self._model_popup.setTarget_(self)
self._model_popup.setAction_("asrModelChanged:")
content.addSubview_(self._model_popup)
```

Add output popup below it:

```python
self._output_mode_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
    NSMakeRect(156, y, 224, 24), False
)
self._output_mode_popup.addItemWithTitle_(t("settings.model.mode_transcribe"))
self._output_mode_popup.addItemWithTitle_(t("settings.model.mode_translate_to_english"))
self._output_mode_popup.selectItemAtIndex_(
    1 if self._prefs.output_mode == OUTPUT_MODE_TRANSLATE_TO_ENGLISH else 0
)
self._output_mode_popup.setTarget_(self)
self._output_mode_popup.setAction_("outputModeChanged:")
content.addSubview_(self._output_mode_popup)
```

- [ ] **Step 4: Add settings actions**

Add methods to `SettingsWindowController`:

```python
    @objc.typedSelector(b"v@:@")
    def asrModelChanged_(self, sender):
        selected_index = sender.indexOfSelectedItem()
        model = list(ASR_MODELS.values())[selected_index]
        old_key = self._prefs.asr_model_key
        self._prefs.asr_model_key = model.key
        if not is_output_mode_supported(model.key, self._prefs.output_mode):
            self._prefs.output_mode = OUTPUT_MODE_TRANSCRIBE
            if self._output_mode_popup is not None:
                self._output_mode_popup.selectItemAtIndex_(0)
        if old_key != model.key:
            transcriber.unload()
        self._refresh_model_controls()

    @objc.typedSelector(b"v@:@")
    def outputModeChanged_(self, sender):
        selected_index = sender.indexOfSelectedItem()
        requested = (
            OUTPUT_MODE_TRANSLATE_TO_ENGLISH
            if selected_index == 1
            else OUTPUT_MODE_TRANSCRIBE
        )
        if is_output_mode_supported(self._prefs.asr_model_key, requested):
            self._prefs.output_mode = requested
        else:
            self._prefs.output_mode = OUTPUT_MODE_TRANSCRIBE
            sender.selectItemAtIndex_(0)
        self._refresh_model_controls()

    def _refresh_model_controls(self):
        model = get_model(self._prefs.asr_model_key)
        translation_supported = is_output_mode_supported(
            model.key, OUTPUT_MODE_TRANSLATE_TO_ENGLISH
        )
        if self._output_mode_popup is not None:
            self._output_mode_popup.itemAtIndex_(1).setEnabled_(translation_supported)
```

- [ ] **Step 5: Add download and delete button behavior**

Add a `Download selected model` button in the model section. Its action should call `transcriber.download_model(self._prefs.asr_model_key)` on a background thread, then refresh status on the main thread. Use the same main-thread selector pattern already used in onboarding.

Add a `Delete selected model` button in the same section. It should:

```text
1. Confirm with an NSAlert using settings.model.delete_confirm_title and settings.model.delete_confirm_message.
2. Call `transcriber.delete_model(self._prefs.asr_model_key)` on a background thread.
3. Delete only the selected model directory under ~/Library/Application Support/vvrite/models/<model_key>.
4. Refresh download status and size labels.
5. Never delete ~/.cache/huggingface automatically.
```

- [ ] **Step 6: Run tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings tests.test_locales tests.test_preferences tests.test_asr_models
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
git add vvrite/settings.py vvrite/locales tests/test_settings.py tests/test_locales.py
git commit -m "feat: add ASR model selection settings"
```

---

### Task 8: Update Main And Onboarding Routing

**Files:**
- Modify: `vvrite/main.py`
- Modify: `vvrite/onboarding.py`
- Modify: `tests/test_preferences.py`
- Modify: `tests/test_transcriber.py`

- [ ] **Step 1: Update app startup cache check**

In `vvrite/main.py`, replace:

```python
transcriber.is_model_cached(self._prefs.model_id)
```

with:

```python
transcriber.is_model_cached(self._prefs.asr_model_key)
```

- [ ] **Step 2: Keep onboarding default simple**

In `vvrite/onboarding.py`, replace raw `self._prefs.model_id` calls with registry-aware display:

```python
model = get_model(self._prefs.asr_model_key)
name_label = NSTextField.labelWithString_(model.display_name)
```

Use `transcriber.get_model_size(self._prefs.asr_model_key)` and `transcriber.download_model(self._prefs.asr_model_key)`.

- [ ] **Step 3: Confirm model switching behavior**

Manual test after implementation:

```text
1. Launch app with Qwen selected.
2. Open Settings.
3. Switch to Whisper large-v3-turbo.
4. Confirm app does not freeze.
5. Confirm no Qwen model remains loaded by checking logs for transcriber.unload.
6. Trigger recording only after selected Whisper model is downloaded.
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_preferences tests.test_transcriber tests.test_settings
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add vvrite/main.py vvrite/onboarding.py tests/test_preferences.py tests/test_transcriber.py
git commit -m "feat: route app startup through selected ASR model"
```

---

### Task 9: Build And Bundle whisper.cpp Sidecar

**Files:**
- Create: `scripts/build_whisper_cpp.sh`
- Modify: `scripts/build.sh`
- Modify: `vvrite.spec`
- Create: `vendor/whisper.cpp/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Add vendor ignore rules**

Update `.gitignore`:

```gitignore
vendor/whisper.cpp/whisper-cli
vendor/whisper.cpp/main
vendor/whisper.cpp/build/
```

Keep `vendor/whisper.cpp/.gitkeep` tracked so the directory exists.

- [ ] **Step 2: Add sidecar build script**

Create `scripts/build_whisper_cpp.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT/build/whisper.cpp"
OUT_DIR="$ROOT/vendor/whisper.cpp"
PINNED_TAG="v1.8.1"

mkdir -p "$BUILD_DIR" "$OUT_DIR"

if [ ! -d "$BUILD_DIR/.git" ]; then
    git clone --depth 1 --branch "$PINNED_TAG" https://github.com/ggml-org/whisper.cpp.git "$BUILD_DIR"
else
    git -C "$BUILD_DIR" fetch --depth 1 origin tag "$PINNED_TAG"
    git -C "$BUILD_DIR" checkout "$PINNED_TAG"
fi

cmake -S "$BUILD_DIR" -B "$BUILD_DIR/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_METAL=ON
cmake --build "$BUILD_DIR/build" -j

if [ -x "$BUILD_DIR/build/bin/whisper-cli" ]; then
    cp "$BUILD_DIR/build/bin/whisper-cli" "$OUT_DIR/whisper-cli"
elif [ -x "$BUILD_DIR/build/bin/main" ]; then
    cp "$BUILD_DIR/build/bin/main" "$OUT_DIR/main"
else
    echo "Unable to find built whisper.cpp CLI binary" >&2
    exit 1
fi

chmod +x "$OUT_DIR/whisper-cli" "$OUT_DIR/main" 2>/dev/null || true
echo "whisper.cpp sidecar ready in $OUT_DIR"
```

- [ ] **Step 3: Add build preflight**

In `scripts/build.sh`, before PyInstaller:

```bash
echo "▸ Building whisper.cpp sidecar..."
"$(dirname "$0")/build_whisper_cpp.sh"
echo "  ✓ whisper.cpp sidecar ready"
```

- [ ] **Step 4: Bundle sidecar in PyInstaller**

In `vvrite.spec`, add to `binaries` or `datas`:

```python
whisper_cli = os.path.join(ROOT_DIR, "vendor", "whisper.cpp", "whisper-cli")
if not os.path.exists(whisper_cli):
    whisper_cli = os.path.join(ROOT_DIR, "vendor", "whisper.cpp", "main")
if not os.path.exists(whisper_cli):
    raise RuntimeError("Missing whisper.cpp sidecar. Run scripts/build_whisper_cpp.sh")
```

Then include:

```python
binaries=[
    (whisper_cli, os.path.join("whisper.cpp", "whisper-cli")),
],
```

- [ ] **Step 5: Sign embedded sidecar**

In `scripts/build.sh`, after signing `.so`/`.dylib` and before signing main executable, add:

```bash
find "$BUNDLE/Contents/Resources/whisper.cpp" -type f -perm +111 2>/dev/null | while read -r bin; do
    codesign --force --options runtime \
        --entitlements "$ENTITLEMENTS" \
        --sign "$IDENTITY" \
        --timestamp \
        "$bin"
done
```

If PyInstaller places the binary under `Contents/MacOS/whisper.cpp`, adjust the path after inspecting the built bundle.

- [ ] **Step 6: Run sidecar build**

Run:

```bash
scripts/build_whisper_cpp.sh
```

Expected: `vendor/whisper.cpp/whisper-cli` or `vendor/whisper.cpp/main` exists and is executable.

- [ ] **Step 7: Commit**

Run:

```bash
git add .gitignore scripts/build_whisper_cpp.sh scripts/build.sh vvrite.spec vendor/whisper.cpp/.gitkeep
git commit -m "build: bundle whisper.cpp sidecar"
```

---

### Task 10: Manual Model Verification

**Files:**
- No required code changes unless failures are found.

- [ ] **Step 1: Confirm Qwen uses app-specific storage after implementation**

Download or load Qwen from onboarding/settings.

Expected:

```text
Qwen model files appear under ~/Library/Application Support/vvrite/models/qwen3_asr_1_7b_8bit/.
No new Qwen download is added to ~/.cache/huggingface/hub by this implementation path.
Existing old Hugging Face cache remains untouched.
```

- [ ] **Step 2: Download Whisper large-v3-turbo from Settings**

Expected:

```text
Download runs in background.
UI stays responsive.
Model file appears under ~/Library/Application Support/vvrite/models/whisper_large_v3_turbo/ggml-large-v3-turbo.bin.
```

- [ ] **Step 3: Test Korean and English mixed transcription with turbo**

Speak:

```text
오늘 회의에서 MLX backend랑 Whisper large v3 turbo를 비교해줘
```

Expected:

```text
Korean remains Korean.
MLX, Whisper, large v3 turbo remain English or recognizable technical terms.
```

- [ ] **Step 4: Download Whisper large-v3**

Expected:

```text
Model file appears under ~/Library/Application Support/vvrite/models/whisper_large_v3/ggml-large-v3.bin.
```

- [ ] **Step 5: Test Korean-to-English translation with large-v3**

Set output mode to `Translate to English`. Speak:

```text
오늘 구현 계획을 체크리스트로 정리하고 성능 리스크도 같이 확인해줘
```

Expected:

```text
English text is inserted into the active app.
No Korean text should be pasted in translation mode.
```

- [ ] **Step 6: Test unsupported translation handling**

Switch model to `Qwen3-ASR` or `Whisper large-v3-turbo`.

Expected:

```text
Translate-to-English option is disabled or automatically reset to Transcribe.
No crash occurs.
```

- [ ] **Step 7: Check idle memory behavior**

Run:

```bash
ps -ef | rg "vvrite|whisper"
```

Expected:

```text
No whisper.cpp process remains after transcription finishes.
Only vvrite remains idle.
```

- [ ] **Step 8: Test model deletion**

Delete `Whisper large-v3-turbo` from Settings.

Expected:

```text
~/Library/Application Support/vvrite/models/whisper_large_v3_turbo/ is removed.
Other model directories remain.
~/.cache/huggingface/hub/ is not modified.
Settings shows the selected model as not downloaded.
```

---

### Task 11: Automated Verification And Build Gate

**Files:**
- Modify only if tests or build fail.

- [ ] **Step 1: Run focused unit tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_asr_models tests.test_model_store tests.test_preferences tests.test_transcriber tests.test_whisper_cpp_backend tests.test_settings tests.test_locales
```

Expected: PASS.

- [ ] **Step 2: Run full unit tests**

Run:

```bash
.venv/bin/python -m unittest discover tests/
```

Expected: PASS unless the current terminal session has no Metal device; if `tests.test_transcriber` fails with `No Metal device available`, record that exact error in the final summary.

- [ ] **Step 3: Run supported build script**

Run:

```bash
./scripts/build.sh
```

Expected:

```text
PyInstaller build succeeds.
whisper.cpp sidecar is included.
Embedded sidecar is signed.
Notarization may fail only if local Apple Developer ID / notarytool credentials are unavailable.
```

Do not run `pyinstaller vvrite.spec` directly.

- [ ] **Step 4: Inspect app bundle for sidecar**

Run:

```bash
find dist/vvrite.app -type f | rg "whisper-cli|/main$"
```

Expected: one bundled whisper.cpp executable path.

- [ ] **Step 5: Commit fixes or final docs**

If changes were needed:

```bash
git add <changed files>
git commit -m "test: verify selectable ASR backends"
```

---

### Task 12: Documentation

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`
- Optionally modify other localized README files if maintaining parity is required.

- [ ] **Step 1: Update model section**

Document:

```markdown
vvrite supports three local ASR models:

| Model | Best for | Approx. size | Translation |
| --- | --- | ---: | --- |
| Qwen3-ASR 1.7B 8-bit | Default multilingual dictation | ~2.5 GB | No |
| Whisper large-v3 | Accuracy and Korean-to-English translation | ~2.9 GiB | Yes, to English |
| Whisper large-v3-turbo | Fast multilingual dictation | ~1.5 GiB | No in vvrite |
```

- [ ] **Step 2: Update privacy section**

Add:

```markdown
All three models run locally. Whisper models are executed through a bundled whisper.cpp sidecar process; no cloud API is required.
```

- [ ] **Step 3: Document model storage and deletion**

Add:

```markdown
Downloaded models are stored under `~/Library/Application Support/vvrite/models/`.
Deleting the vvrite app bundle does not automatically delete downloaded models.
Use Settings > Model > Delete selected model to reclaim disk space, or remove the model folders manually.
Older vvrite builds may also have cached Qwen files under `~/.cache/huggingface/hub/`.
```

- [ ] **Step 4: Update license section**

Mention:

```markdown
whisper.cpp is MIT licensed. Whisper model weights are distributed through the ggerganov/whisper.cpp Hugging Face repository. Qwen3-ASR remains Apache 2.0.
```

- [ ] **Step 5: Run README grep sanity check**

Run:

```bash
rg -n "Qwen3-ASR|Whisper|large-v3|translation|Application Support|Delete selected model|local" README.md README.ko.md
```

Expected: docs mention all three models and translation limitation.

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md README.ko.md
git commit -m "docs: document selectable ASR models"
```

---

## Final Acceptance Checklist

- [ ] Settings offers exactly three ASR models: Qwen3-ASR 1.7B 8-bit, Whisper large-v3, Whisper large-v3-turbo.
- [ ] Qwen remains the default for existing and new users.
- [ ] Existing `model_id` preference does not break old installs.
- [ ] Only selected model is loaded/executed.
- [ ] Whisper subprocess exits after each transcription.
- [ ] English translation mode is available only for Whisper large-v3.
- [ ] Korean transcription works.
- [ ] Korean/English mixed transcription keeps English technical terms in English where the model recognizes them.
- [ ] Korean-to-English translation works with Whisper large-v3.
- [ ] Unsupported translation mode cannot crash the app.
- [ ] Model download status is visible in Settings.
- [ ] All newly downloaded model files live under `~/Library/Application Support/vvrite/models/`.
- [ ] Existing old Hugging Face cache content is not deleted automatically.
- [ ] Settings can delete each downloaded model independently.
- [ ] Deleting the app bundle is documented as not deleting downloaded models automatically.
- [ ] App UI remains responsive during model download and transcription.
- [ ] `./scripts/build.sh` remains the only build path.
- [ ] `whisper.cpp` sidecar is signed inside the app bundle.
- [ ] README documents model choices, disk usage, local-only behavior, and translation limits.

## Expected Effort

- Model registry and preferences: 2-4 hours.
- Backend split and Whisper subprocess integration: 6-10 hours.
- Settings UI and localization: 5-10 hours.
- Build/bundling/signing integration: 6-12 hours.
- Manual model verification and docs: 4-8 hours.
- Total realistic estimate: 3-5 focused engineering days including build/distribution hardening.
- Minimal developer-only prototype without notarized distribution: 1.5-2 days.

## Handoff Notes For Next Session

Start with:

```bash
git status --short --branch
sed -n '1,220p' docs/superpowers/plans/2026-04-25-whisper-backends.md
```

Then implement from Task 1 downward. Commit after each task. Do not skip Task 8 because a locally working subprocess path is not enough for a distributed macOS app.
