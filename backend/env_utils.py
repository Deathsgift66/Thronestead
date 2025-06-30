"""Utility functions for resilient environment variable access."""
from __future__ import annotations
import os

FALLBACK_PREFIXES = ["", "BACKUP_", "FALLBACK_", "DEFAULT_"]


def get_env_var(key: str, default: str | None = None) -> str | None:
    """Return the first available environment variable among fallbacks.

    The search order checks ``key`` itself followed by names with the prefixes
    ``BACKUP_``, ``FALLBACK_``, and ``DEFAULT_``. The first non-empty value is
    returned. If none are found, ``default`` is returned.
    """
    for prefix in FALLBACK_PREFIXES:
        val = os.getenv(f"{prefix}{key}")
        if val:
            return val
    return default
