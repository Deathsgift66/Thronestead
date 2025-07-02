# Project Name: Thronestead©
# File Name: targeting.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Utilities for selecting combat targets and applying unit counters."""

from functools import lru_cache
from typing import Any, Dict, List

# Database interface for counters
from ..db import db


def select_target(
    unit: Dict[str, Any], enemies_in_range: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Select the best target for ``unit`` from ``enemies_in_range``."""

    priority_list = unit.get("target_priority") or []

    for priority_type in priority_list:
        target = next(
            (e for e in enemies_in_range if e.get("unit_type") == priority_type),
            None,
        )
        if target:
            return target

    # Fallback to the nearest enemy if no priority match found
    position_x = unit.get("position_x")
    position_y = unit.get("position_y")

    return min(
        enemies_in_range,
        key=lambda e: max(
            abs(position_x - e.get("position_x")),
            abs(position_y - e.get("position_y")),
        ),
    )


@lru_cache(maxsize=256)
def get_counter_multiplier(attacker_type: str, defender_type: str) -> float:
    """Return the counter effectiveness multiplier.

    Results are cached to avoid repeated database lookups during combat.
    """

    rows = db.query(
        """
        SELECT effectiveness_multiplier
        FROM unit_counters
        WHERE unit_type = %s AND countered_unit_type = %s
        """,
        (attacker_type, defender_type),
    )

    if rows:
        return float(rows[0].get("effectiveness_multiplier", 1.0))
    return 1.0
