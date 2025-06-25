# Project Name: Thronestead©
# File Name: modifiers_utils.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
"""Shared utilities for modifier handling."""

# Cached modifier data to reduce expensive aggregation queries.
_modifier_cache: dict[int, tuple[float, dict]] = {}


def _merge_modifiers(target: dict, mods: dict) -> None:
    """Deep-merge modifier dictionaries into the target dict."""
    if not isinstance(mods, dict):
        return
    for cat, inner in mods.items():
        if not isinstance(inner, dict):
            continue
        bucket = target.setdefault(cat, {})
        for key, val in inner.items():
            bucket[key] = bucket.get(key, 0) + val


def invalidate_cache(kingdom_id: int) -> None:
    """Clear cached modifiers for the given kingdom."""
    _modifier_cache.pop(kingdom_id, None)
