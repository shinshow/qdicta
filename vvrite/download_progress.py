"""Formatting helpers for model download progress."""


def format_bytes(value: int) -> str:
    amount = float(max(0, int(value)))
    units = ["B", "KiB", "MiB", "GiB"]
    unit = units[0]
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            break
        amount /= 1024
    if unit == "B":
        return f"{int(amount)} {unit}"
    return f"{amount:.1f} {unit}"


def format_progress(downloaded: int, total: int) -> str:
    if total > 0:
        percent = min(100, int((downloaded / total) * 100))
        return f"{format_bytes(downloaded)} / {format_bytes(total)} ({percent}%)"
    return f"{format_bytes(downloaded)} downloaded"
