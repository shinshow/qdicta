"""Whisper backend using a bundled whisper.cpp sidecar."""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request

from vvrite import audio_utils, model_store
from vvrite.asr_models import OUTPUT_MODE_TRANSLATE_TO_ENGLISH


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
