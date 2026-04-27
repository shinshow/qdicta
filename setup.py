"""py2app build configuration for Qdicta."""
import os
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

sys.setrecursionlimit(5000)

from setuptools import setup
from vvrite import APP_BUNDLE_IDENTIFIER, APP_NAME, __version__

APP = ["vvrite/main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": APP_NAME,
        "CFBundleIdentifier": APP_BUNDLE_IDENTIFIER,
        "CFBundleShortVersionString": __version__,
        "CFBundleVersion": "16",
        "LSUIElement": True,
        "NSMicrophoneUsageDescription": (
            f"{APP_NAME} needs microphone access to record and transcribe your speech."
        ),
        "NSHighResolutionCapable": True,
    },
    "packages": [
        "vvrite",
        "mlx",
        "mlx_audio",
        "mlx_whisper",
        "mlx_lm",
        "transformers",
        "tiktoken",
        "scipy",
        "sounddevice",
        "soundfile",
        "numpy",
        "huggingface_hub",
    ],
    "includes": [
        "Quartz",
        "AppKit",
        "Foundation",
        "ApplicationServices",
        "ServiceManagement",
        "objc",
    ],
    "excludes": [
        "tkinter",
        "unittest",
        "test",
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
