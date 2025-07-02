"""Utility functions for resilient environment variable access."""
from __future__ import annotations
from distutils.util import strtobool as _std_strtobool
import os

VARIANT_PREFIXES = ["", "VITE_", "PUBLIC_", "PUBLIC_VITE_"]


def get_env_var(key: str, default: str | None = None) -> str | None:
    """Return the first available environment variable among fallbacks.

    The search order checks ``key`` itself as well as variants prefixed with
    ``VITE_`` and ``PUBLIC_``. The first non-empty value is returned. If none
    are found, ``default`` is returned.
    """
    for variant in VARIANT_PREFIXES:
        val = os.getenv(f"{variant}{key}")
        if val:
            return val
    return default


def strtobool(val: str) -> bool:
    """Return ``True`` for truthy strings and ``False`` for falsey ones."""
    return bool(_std_strtobool(val))

