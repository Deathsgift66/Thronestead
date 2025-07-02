"""Utility functions for resilient environment variable access."""
from __future__ import annotations
import os

TRUTHY = {"1", "true", "t", "yes", "y", "on"}
FALSEY = {"0", "false", "f", "no", "n", "off"}

VARIANT_PREFIXES = ["", "VITE_", "PUBLIC_", "PUBLIC_VITE_"]


def get_env_var(key: str, default: str | None = None) -> str | None:
    """Return the first defined environment variable matching ``key`` variants."""

    for name in (f"{pref}{key}" for pref in VARIANT_PREFIXES):
        val = os.getenv(name)
        if val:
            return val
    return default


def strtobool(val: str) -> bool:
    """Return ``True`` for truthy strings and ``False`` for falsy ones."""
    val_lc = val.strip().lower()
    if val_lc in TRUTHY:
        return True
    if val_lc in FALSEY:
        return False
    raise ValueError(f"invalid truth value {val!r}")


def get_env_bool(key: str, default: bool = False) -> bool:
    """Return an environment variable as a bool with sensible defaults."""
    val = get_env_var(key)
    return strtobool(val) if val is not None else default


