"""Utility functions for resilient environment variable access."""
from __future__ import annotations
from distutils.util import strtobool as _std_strtobool
import os

VARIANT_PREFIXES = ["", "VITE_", "PUBLIC_", "PUBLIC_VITE_"]


def get_env_var(key: str, default: str | None = None) -> str | None:
    """Return the first defined environment variable matching ``key`` variants."""

    for name in (f"{pref}{key}" for pref in VARIANT_PREFIXES):
        val = os.getenv(name)
        if val:
            return val
    return default


def strtobool(val: str) -> bool:
    """Return ``True`` for truthy strings and ``False`` for falsey ones."""
    return bool(_std_strtobool(val))


def get_env_bool(key: str, default: bool = False) -> bool:
    """Return an environment variable as a bool with sensible defaults."""
    val = get_env_var(key)
    return strtobool(val) if val is not None else default


