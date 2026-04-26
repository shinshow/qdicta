"""Helpers for transcribing existing media files."""

from __future__ import annotations

import os
import shutil
import tempfile

SUPPORTED_MEDIA_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".mp4",
    ".caf",
    ".aiff",
    ".flac",
}


def is_supported_media_file(path: str) -> bool:
    return os.path.splitext(str(path))[1].lower() in SUPPORTED_MEDIA_EXTENSIONS


def prepare_transcription_input(path: str) -> str:
    if not is_supported_media_file(path):
        raise ValueError(f"Unsupported media file: {path}")

    suffix = os.path.splitext(path)[1].lower()
    fd, dest = tempfile.mkstemp(prefix="vvrite_file_", suffix=suffix)
    os.close(fd)
    shutil.copyfile(path, dest)
    return dest
