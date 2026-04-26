# Changelog

All notable changes to this fork are documented here.

## Unreleased

### Changed

- Replaced the selectable Whisper options with MLX-native `whisper-small-4bit` and `whisper-large-v3-turbo-4bit` models.
- Added an MLX Whisper backend that downloads Hugging Face snapshots into vvrite's app-managed model directory and warms up the selected model before dictation.
- Removed the PyInstaller build-time requirement for bundled whisper.cpp sidecar binaries.

## [1.1.0] - 2026-04-26

Compared with upstream `shaircast/vvrite` `v1.0.6`, this release adds selectable local ASR models, improves model lifecycle handling, and updates the app to use this fork's GitHub releases for update checks.

### Added

- Added selectable ASR models in Settings: Qwen3-ASR 1.7B 8-bit, Whisper large-v3, and Whisper large-v3-turbo.
- Added app-managed model storage under `~/Library/Application Support/vvrite/models/`.
- Added model download progress, cached-model detection, and selected-model deletion controls.
- Added Whisper support through bundled whisper.cpp binaries and model downloads from Hugging Face.
- Added English translation mode for Whisper large-v3.
- Added persistent version history in `CHANGELOG.md`.

### Changed

- Bumped app version from `1.0.6` to `1.1.0`.
- Changed update checks to use `https://github.com/shinshow/vvrite` releases.
- Updated README documentation for selectable ASR models and fork installation URLs.
- Improved Qwen model loading so it uses the app-managed model directory.
- Improved Whisper Turbo response time by keeping the selected whisper.cpp model loaded and using fast greedy decode defaults.
- Made model switching prepare the selected model immediately: downloaded models are loaded, missing models are downloaded first.

### Fixed

- Fixed `Qwen3-ASR model is not loaded` after switching from a downloaded Whisper model back to Qwen.
- Fixed model switch behavior so the previous backend is unloaded before the selected backend is activated.
- Fixed Whisper fallback CLI defaults to avoid expensive beam/best-of decoding for dictation.
