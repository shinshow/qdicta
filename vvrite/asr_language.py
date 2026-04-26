"""ASR language hint resolution."""


def resolve_asr_language(prefs) -> str:
    """Return the concrete ASR language code to send to model backends."""
    selected = str(getattr(prefs, "asr_language", "auto") or "auto")
    if selected != "auto":
        return selected

    return "auto"
