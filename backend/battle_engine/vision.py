"""Utility functions for unit vision calculations."""

from __future__ import annotations

from typing import Any, Dict, List

# Database interface for unit vision updates
from ..db import db


def process_unit_vision(unit: Dict[str, Any], all_units: List[Dict[str, Any]], terrain: List[List[str]]) -> None:
    """Update ``unit`` visible enemies based on vision range and terrain."""

    unit_id = unit["movement_id"]
    unit_stats = db.query(
        """
        SELECT vision FROM unit_stats WHERE unit_type = %s
        """,
        (unit["unit_type"],),
    ).first()

    vision_range = unit_stats["vision"] if unit_stats else 0
    position_x = unit["position_x"]
    position_y = unit["position_y"]

    visible_enemy_ids: List[int] = []

    for other in all_units:
        if other["kingdom_id"] == unit["kingdom_id"]:
            continue

        dx = abs(position_x - other["position_x"])
        dy = abs(position_y - other["position_y"])
        distance = max(dx, dy)

        mid_x = (position_x + other["position_x"]) // 2
        mid_y = (position_y + other["position_y"]) // 2
        terrain_type = terrain[mid_y][mid_x]

        vision_penalty = terrain_vision_modifier(terrain_type)
        effective_vision = vision_range / vision_penalty

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

    if terrain_type == "plains":
        return 1.0
    if terrain_type == "forest":
        return 2.0
    if terrain_type == "hill":
        return 0.75
    if terrain_type == "river":
        return 1.5
    if terrain_type == "bridge":
        return 1.0
    return 1.0
