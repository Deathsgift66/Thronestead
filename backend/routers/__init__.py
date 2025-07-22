# Project Name: Thronestead©
# File Name: __init__.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Router package with lazy module loading."""

from __future__ import annotations

import importlib
import pkgutil

_modules = [name for _, name, _ in pkgutil.iter_modules(__path__) if not name.startswith("_")]
# Exclude individual alliance router modules in favor of the consolidated one
ALLIANCE_MODULE_PREFIX = "alliance_"
__all__ = [
    name
    for name in _modules
    if not (name.startswith(ALLIANCE_MODULE_PREFIX) and name != "alliance_router")
]


def __getattr__(name: str):
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__} has no attribute {name}")
