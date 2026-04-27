# Privacy

vvrite is designed as an on-device dictation app for macOS. This document describes what data the app uses and where it is stored.

## Audio and Media Files

vvrite records microphone audio only while you start a recording with the configured hotkey. Audio is saved temporarily for local transcription, then the temporary audio files are deleted after transcription completes or recording is canceled.

When you use file transcription, vvrite copies the selected audio/video file to a temporary working file before passing it to the local transcription backend. The original selected file is not modified by vvrite.

Audio is processed locally on your Mac using MLX-based ASR models. vvrite does not upload recorded audio to a cloud transcription service.

## Transcribed Text and Clipboard

When transcription succeeds, vvrite writes the transcribed text to the macOS clipboard, sends a paste command to the active app, then restores the previous clipboard contents after a short delay.

The most recent pasted dictation result may be kept in memory so the optional retract shortcut can delete that text.

vvrite also keeps a local recent dictation history so the menu bar can show **Recent Dictations...** and **Copy Last Dictation**. By default, the history keeps up to 10 recent non-empty results and is stored locally at:

```text
~/Library/Application Support/vvrite/history.json
```

This history is not uploaded by vvrite.

## Permissions

vvrite asks macOS for:

- Microphone access, to record speech.
- Accessibility access, to listen for the global hotkey and paste text into the active app.

These permissions are controlled by macOS System Settings.

## Local Storage

vvrite stores preferences in macOS user defaults. Downloaded model files are stored under:

```text
~/Library/Application Support/vvrite/models/
```

Deleting the app from `/Applications` does not automatically delete downloaded models. You can remove models from vvrite settings or delete the model folder manually.

## Network Access

vvrite uses network access for:

- Downloading selected ASR model files from Hugging Face.
- Checking GitHub Releases for updates when update checks are enabled.

The app does not operate a separate analytics, telemetry, advertising, or cloud transcription service.

## Updates

For direct distribution, vvrite may check the project's GitHub Releases page for newer versions. Update checks send a standard HTTPS request to GitHub. Downloading and installing an update remains under the user's control.
