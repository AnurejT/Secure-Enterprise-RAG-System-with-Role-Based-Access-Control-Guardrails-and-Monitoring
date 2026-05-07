"""
backend/common/helpers.py
Shared utility helpers used across the backend.
"""


def truncate(text: str, max_len: int = 200) -> str:
    """Safely truncate a string to max_len characters."""
    if not text:
        return ""
    return text[:max_len] + ("..." if len(text) > max_len else "")


def safe_get(d: dict, *keys, default=None):
    """Safely navigate a nested dict with multiple keys."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d
