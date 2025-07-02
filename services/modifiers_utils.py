# Project Name: Thronestead©
# File Name: modifiers_utils.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Shared utilities for modifier handling."""

import logging
import json

# Cached modifier data to reduce expensive aggregation queries.
_modifier_cache: dict[int, tuple[float, dict]] = {}


logger = logging.getLogger(__name__)


def parse_json_field(value):
    """Return ``value`` parsed as JSON when it's a string."""
    if isinstance(value, str):
        try:
            return json.loads(value) or {}
        except Exception:
            return {}
    return value or {}


def _merge_modifiers(target: dict, mods: dict) -> None:
    """Deep-merge modifier dictionaries into the target dict with validation."""
    if not isinstance(mods, dict) or not mods:
        return

    for cat, inner in mods.items():
        if not isinstance(inner, dict):
            continue
        bucket = target.setdefault(cat, {})
        for key, val in inner.items():
            try:
                num = float(val)
            except (TypeError, ValueError):
                continue
            bucket[key] = bucket.get(key, 0) + num


def invalidate_cache(kingdom_id: int) -> None:
    """Clear cached modifiers for the given kingdom."""
    _modifier_cache.pop(kingdom_id, None)
