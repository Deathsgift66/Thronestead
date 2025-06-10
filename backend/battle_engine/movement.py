"""Utility functions for tactical unit movement."""

from __future__ import annotations

from typing import Any, Dict, List

# Database interface for persisting movement state
from ..db import db


def process_unit_movement(unit: Dict[str, Any], terrain: List[List[str]]) -> None:
    """Move a unit on the 20x60 grid and persist its position."""

    unit_id = unit["movement_id"]
    stance = unit["stance"]
    speed = unit["speed"]

    movement_path = unit.get("movement_path") or []
    patrol_zone = unit.get("patrol_zone") or {}
    fallback_x = unit.get("fallback_point_x")
    fallback_y = unit.get("fallback_point_y")
    withdraw_threshold = unit.get("withdraw_threshold_percent") or 0
    morale = unit.get("morale") or 1.0

    if unit.get("withdraw_threshold_percent", 0) > 0 and morale < (withdraw_threshold / 100):
        move_towards(unit, fallback_x, fallback_y, speed, terrain)
        update_unit_position(unit_id, unit["position_x"], unit["position_y"])
        return

    if stance == "hold_ground":
        return

    if stance == "advance_engage" and movement_path:
        next_tile = movement_path[0]
        reached = move_towards(unit, next_tile["x"], next_tile["y"], speed, terrain)
        if reached:
            movement_path.pop(0)
            db.execute(
                """UPDATE unit_movements SET movement_path = %s WHERE movement_id = %s""",
                (movement_path, unit_id),
            )
        update_unit_position(unit_id, unit["position_x"], unit["position_y"])
        return

    if stance == "patrol_zone" and patrol_zone:
        patrol_target = select_patrol_target(unit, patrol_zone)
        move_towards(unit, patrol_target["x"], patrol_target["y"], speed, terrain)
        update_unit_position(unit_id, unit["position_x"], unit["position_y"])
        return

    if movement_path:
        next_tile = movement_path[0]
        reached = move_towards(unit, next_tile["x"], next_tile["y"], speed, terrain)
        if reached:
            movement_path.pop(0)
            db.execute(
                """UPDATE unit_movements SET movement_path = %s WHERE movement_id = %s""",
                (movement_path, unit_id),
            )
        update_unit_position(unit_id, unit["position_x"], unit["position_y"])


def move_towards(unit: Dict[str, Any], target_x: int, target_y: int, speed: int, terrain: List[List[str]]) -> bool:
    """Move ``unit`` toward ``target_x`` and ``target_y``. Return ``True`` if reached."""

    cur_x = unit["position_x"]
    cur_y = unit["position_y"]

    dx = target_x - cur_x
    dy = target_y - cur_y

    if dx == 0 and dy == 0:
        return True

    move_x = min(speed, abs(dx)) * (1 if dx > 0 else -1 if dx < 0 else 0)
    move_y = min(speed, abs(dy)) * (1 if dy > 0 else -1 if dy < 0 else 0)

    terrain_type = terrain[cur_y][cur_x]
    movement_penalty = terrain_movement_modifier(terrain_type, unit)

    move_x = int(move_x / movement_penalty)
    move_y = int(move_y / movement_penalty)

    new_x = max(0, min(59, cur_x + move_x))
    new_y = max(0, min(19, cur_y + move_y))

    unit["position_x"] = new_x
    unit["position_y"] = new_y

    return new_x == target_x and new_y == target_y


def terrain_movement_modifier(terrain_type: str, unit: Dict[str, Any]) -> float:
    """Return movement penalty multiplier based on terrain and unit type."""

    if terrain_type == "plains":
        return 1.0
    if terrain_type == "forest":
        return 2.0 if unit.get("class") == "cavalry" else 1.5
    if terrain_type == "river":
        return 1.0 if unit.get("can_build_bridge") else 999
    if terrain_type == "hills":
        return 1.5
    if terrain_type == "bridge":
        return 1.0
    return 1.0


def select_patrol_target(unit: Dict[str, Any], patrol_zone: Dict[str, int]) -> Dict[str, int]:
    """Return a random tile within ``patrol_zone`` for patrolling units."""

    import random

    x1 = patrol_zone.get("x1", 0)
    y1 = patrol_zone.get("y1", 0)
    x2 = patrol_zone.get("x2", 59)
    y2 = patrol_zone.get("y2", 19)

    target_x = random.randint(min(x1, x2), max(x1, x2))
    target_y = random.randint(min(y1, y2), max(y1, y2))

    return {"x": target_x, "y": target_y}


def update_unit_position(unit_id: int, x: int, y: int) -> None:
    """Persist the unit position using ``db``. No-op if ``db`` is a dummy."""

    db.execute(
        """
        UPDATE unit_movements
        SET position_x = %s, position_y = %s, last_updated = now()
        WHERE movement_id = %s
        """,
        (x, y, unit_id),
    )
