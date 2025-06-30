# Project Name: Thronestead©
# File Name: env_utils.py
# Version: 2025-06-25
# Developer: Codex
"""Utility helpers for robust environment variable access."""

from __future__ import annotations

import os
from pathlib import Path


# Load defaults from .env.example if available
_DEFAULTS: dict[str, str] = {}
_env_example = Path(__file__).resolve().parent.parent / ".env.example"
if _env_example.exists():
    try:
        with _env_example.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                _DEFAULTS[k.strip()] = v.strip()
    except Exception:
        # Do not crash if defaults fail to load
        pass


def get_env(*names: str, default: str | None = None) -> str | None:
    """Return the first environment variable value found in ``names``.

    If none are present, fall back to any matching value loaded from
    ``.env.example``. Finally return ``default``.
    """
    for name in names:
        val = os.getenv(name)
        if val is not None:
            return val
    for name in names:
        if name in _DEFAULTS:
            return _DEFAULTS[name]
    return default
