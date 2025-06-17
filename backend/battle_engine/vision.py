# Project Name: Thronestead©
# File Name: vision.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""Utility functions for unit vision calculations."""

from typing import Any, Dict, List

# Database interface for unit vision updates
from ..db import db

# Pre-calculated terrain vision penalties for quick lookup
_VISION_PENALTIES: Dict[str, float] = {
    "plains": 1.0,
    "forest": 2.0,
    "hills": 0.75,
    "river": 1.5,
    "bridge": 1.0,
}


def process_unit_vision(
    unit: Dict[str, Any], all_units: List[Dict[str, Any]], terrain: List[List[str]]
) -> None:
    """Update ``unit`` visible enemies based on vision range and surrounding terrain."""

    unit_id = unit["movement_id"]
    rows = db.query(
        """
        SELECT vision FROM unit_stats WHERE unit_type = %s
        """,
        (unit["unit_type"],),
    )

    vision_range = rows[0]["vision"] if rows else 0
    position_x = unit["position_x"]
    position_y = unit["position_y"]

    visible_enemy_ids: List[int] = []

    if not all_units:
        db.execute(
            """
            UPDATE unit_movements
            SET visible_enemies = %s
            WHERE movement_id = %s
            """,
            (visible_enemy_ids, unit_id),
        )
        return

    for other in all_units:
        if other["kingdom_id"] == unit["kingdom_id"]:
            continue

        dx = abs(position_x - other["position_x"])
        dy = abs(position_y - other["position_y"])
        distance = max(dx, dy)

        mid_x = (position_x + other["position_x"]) // 2
        mid_y = (position_y + other["position_y"]) // 2
        terrain_type = terrain[mid_y][mid_x]

        penalty = _VISION_PENALTIES.get(terrain_type, 1.0)
        effective_vision = vision_range / penalty

        if distance <= effective_vision:
            visible_enemy_ids.append(other["movement_id"])

    db.execute(
        """
        UPDATE unit_movements
        SET visible_enemies = %s
        WHERE movement_id = %s
        """,
        (visible_enemy_ids, unit_id),
    )


def terrain_vision_modifier(terrain_type: str) -> float:
    """Return vision penalty multiplier based on ``terrain_type``."""

    return _VISION_PENALTIES.get(terrain_type, 1.0)
