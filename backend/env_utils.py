"""Utility functions for resilient environment variable access."""
from __future__ import annotations
import os
from functools import lru_cache

TRUTHY = {"1", "true", "t", "yes", "y", "on"}
FALSEY = {"0", "false", "f", "no", "n", "off"}

VARIANT_PREFIXES = ["", "VITE_", "PUBLIC_", "PUBLIC_VITE_"]


@lru_cache(maxsize=None)
def get_env_var(key: str, default: str | None = None) -> str | None:
    """Return the value of the first defined variant of ``key``.

    The result is cached since environment variables rarely change at runtime.
    """

    for pref in VARIANT_PREFIXES:
        val = os.getenv(f"{pref}{key}")
        if val is not None:
            return val
    return default


def strtobool(val: str) -> bool:
    """Return ``True`` for truthy strings and ``False`` for falsy ones."""
    val_lower = val.strip().lower()
    if val_lower in TRUTHY:
        return True
    if val_lower in FALSEY:
        return False
    raise ValueError(f"invalid truth value {val!r}")


def get_env_bool(key: str, default: bool = False) -> bool:
    """Return an environment variable as a bool with sensible defaults."""
    val = get_env_var(key)
    return strtobool(val) if val is not None else default


