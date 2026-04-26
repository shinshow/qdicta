"""ASR language hint resolution."""

from vvrite.locales import ASR_LANGUAGE_MAP, resolve_system_locale


def resolve_asr_language(prefs) -> str:
    """Return the concrete ASR language code to send to model backends."""
    selected = str(getattr(prefs, "asr_language", "auto") or "auto")
    if selected != "auto":
        return selected

    ui_language = getattr(prefs, "ui_language", None)
    if ui_language in ASR_LANGUAGE_MAP:
        return str(ui_language)

    system_language = resolve_system_locale()
    if system_language in ASR_LANGUAGE_MAP:
        return system_language

    return "auto"
