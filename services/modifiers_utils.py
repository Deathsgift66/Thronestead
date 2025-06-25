# Project Name: Thronestead©
# File Name: modifiers_utils.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
"""Shared utilities for modifier handling."""

import logging

# Cached modifier data to reduce expensive aggregation queries.
_modifier_cache: dict[int, tuple[float, dict]] = {}


logger = logging.getLogger(__name__)


def _merge_modifiers(target: dict, mods: dict) -> None:
    """Deep-merge modifier dictionaries into the target dict with validation."""
    if not isinstance(mods, dict):
        return
    for cat, inner in mods.items():
        if not isinstance(inner, dict):
            continue
        bucket = target.setdefault(cat, {})
        for key, val in inner.items():
            try:
                num = float(val)
            except (TypeError, ValueError):
                logger.debug("Ignoring non-numeric modifier %s.%s", cat, key)
                continue
            if key in bucket:
                logger.debug("Accumulating duplicate modifier %s.%s", cat, key)
            bucket[key] = bucket.get(key, 0) + num


def invalidate_cache(kingdom_id: int) -> None:
    """Clear cached modifiers for the given kingdom."""
    _modifier_cache.pop(kingdom_id, None)
