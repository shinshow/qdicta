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
