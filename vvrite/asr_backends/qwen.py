"""Qwen3-ASR backend using mlx-audio."""

import concurrent.futures
import os
import tempfile
import threading

import numpy as np
import soundfile as sf
from huggingface_hub import model_info, snapshot_download

from vvrite import audio_utils, model_store
from vvrite.locales import ASR_LANGUAGE_MAP
from vvrite.preferences import SAMPLE_RATE

_MODEL_KEY = "qwen3_asr_1_7b_8bit"
_model = None
_warmed_up = False
_worker_thread_id = None


def _worker_initializer():
    global _worker_thread_id
    _worker_thread_id = threading.get_ident()


_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="vvrite-qwen-mlx",
    initializer=_worker_initializer,
)


def _run_on_worker(func, *args, **kwargs):
    if threading.get_ident() == _worker_thread_id:
        return func(*args, **kwargs)
    return _executor.submit(func, *args, **kwargs).result()


def is_loaded() -> bool:
    return _model is not None


def _unload_impl():
    global _model, _warmed_up
    _model = None
    _warmed_up = False


def unload():
    _run_on_worker(_unload_impl)


def is_cached(model_id: str) -> bool:
    local_dir = model_store.model_dir(_MODEL_KEY)
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


def download(model_id: str, progress_callback=None) -> str:
    local_dir = model_store.model_dir(_MODEL_KEY)
    if progress_callback is not None:
        progress_callback(0, 0)
    return snapshot_download(repo_id=model_id, local_dir=local_dir)


def load_from_local(local_path: str):
    _run_on_worker(_load_from_local_impl, local_path)


def _load_from_local_impl(local_path: str):
    from mlx_audio.stt.utils import load_model

    global _model, _warmed_up
    _model = load_model(local_path)
    _warmed_up = False
    safe_warm_up()


def load(model_id: str):
    load_from_local(model_store.model_dir(_MODEL_KEY))


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
    return _run_on_worker(_transcribe_impl, raw_wav_path, prefs)


def _transcribe_impl(raw_wav_path: str, prefs) -> str:
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
                print(
                    f"Unknown ASR language code: {asr_lang}, falling back to auto-detect"
                )
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
