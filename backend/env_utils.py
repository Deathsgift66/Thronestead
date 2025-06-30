"""Utility functions for resilient environment variable access."""
from __future__ import annotations
import os

FALLBACK_PREFIXES = ["", "BACKUP_", "FALLBACK_", "DEFAULT_"]
VARIANT_PREFIXES = ["", "VITE_", "PUBLIC_", "PUBLIC_VITE_"]


def get_env_var(key: str, default: str | None = None) -> str | None:
    """Return the first available environment variable among fallbacks.

    The search order checks ``key`` itself as well as variants prefixed with
    ``VITE_`` and ``PUBLIC_``. Each variant is additionally checked with the
    prefixes ``BACKUP_``, ``FALLBACK_``, and ``DEFAULT_``. The first non-empty
    value is returned. If none are found, ``default`` is returned.
    """
    for prefix in FALLBACK_PREFIXES:
        for variant in VARIANT_PREFIXES:
            val = os.getenv(f"{prefix}{variant}{key}")
            if val:
                return val
    return default


def strtobool(val: str) -> bool:
    """Return ``True`` for truthy strings and ``False`` for falsey ones."""
    v = val.strip().lower()
    if v in ("y", "yes", "t", "true", "on", "1"):
        return True
    if v in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"invalid truth value {val!r}")

