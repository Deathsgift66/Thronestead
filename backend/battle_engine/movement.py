# Project Name: Thronestead©
# File Name: movement.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""Utility functions for tactical unit movement."""

from typing import Any, Dict, List, Deque
from collections import deque
import random

# Database interface for persisting movement state
from ..db import db

# Base movement penalties by terrain type
TERRAIN_BASE_MODIFIERS: Dict[str, float] = {
    "plains": 1.0,
    "forest": 1.5,
    "hills": 1.5,
    "bridge": 1.0,
    "river": 1.0,  # default when unit can build bridges
}


def process_unit_movement(unit: Dict[str, Any], terrain: List[List[str]]) -> None:
    """Advance ``unit`` based on stance, path, and morale, persisting position."""

    unit_id = unit["movement_id"]
    stance = unit["stance"]
    speed = unit["speed"]

    movement_path: Deque[Dict[str, int]] = deque(unit.get("movement_path") or [])
    patrol_zone = unit.get("patrol_zone") or {}
    fallback_x = unit.get("fallback_point_x")
    fallback_y = unit.get("fallback_point_y")
    withdraw_threshold = unit.get("withdraw_threshold_percent", 0)
    morale = unit.get("morale") or 1.0

    if withdraw_threshold > 0 and morale < (withdraw_threshold / 100):
        move_towards(unit, fallback_x, fallback_y, speed, terrain)
        update_unit_position(unit_id, unit["position_x"], unit["position_y"])
        return

    if stance == "hold_ground":
        return

    if stance == "advance_engage" and movement_path:
        if advance_along_path(unit, movement_path, speed, terrain):
            persist_movement_path(unit_id, movement_path)
        update_unit_position(unit_id, unit["position_x"], unit["position_y"])
        return

    if stance == "patrol_zone" and patrol_zone:
        patrol_target = select_patrol_target(unit, patrol_zone)
        move_towards(unit, patrol_target["x"], patrol_target["y"], speed, terrain)
        update_unit_position(unit_id, unit["position_x"], unit["position_y"])
        return

    if movement_path:
        if advance_along_path(unit, movement_path, speed, terrain):
            persist_movement_path(unit_id, movement_path)
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

    base = TERRAIN_BASE_MODIFIERS.get(terrain_type, 1.0)

    if terrain_type == "forest" and unit.get("class") == "cavalry":
        return 2.0
    if terrain_type == "river":
        return 1.0 if unit.get("can_build_bridge") else 999

    return base


def select_patrol_target(unit: Dict[str, Any], patrol_zone: Dict[str, int]) -> Dict[str, int]:
    """Return a random tile within ``patrol_zone`` for patrolling units."""

    x1 = patrol_zone.get("x1", 0)
    y1 = patrol_zone.get("y1", 0)
    x2 = patrol_zone.get("x2", 59)
    y2 = patrol_zone.get("y2", 19)

    min_x, max_x = sorted((x1, x2))
    min_y, max_y = sorted((y1, y2))
    target_x = random.randint(min_x, max_x)
    target_y = random.randint(min_y, max_y)

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


def advance_along_path(
    unit: Dict[str, Any],
    path: Deque[Dict[str, int]],
    speed: int,
    terrain: List[List[str]],
) -> bool:
    """Advance ``unit`` toward the next waypoint in ``path``."""

    if not path:
        return False

    next_tile = path[0]
    reached = move_towards(unit, next_tile["x"], next_tile["y"], speed, terrain)
    if reached:
        path.popleft()
    return reached


def persist_movement_path(unit_id: int, path: Deque[Dict[str, int]]) -> None:
    """Persist updated movement path to the database."""

    db.execute(
        """UPDATE unit_movements SET movement_path = %s WHERE movement_id = %s""",
        (list(path), unit_id),
    )
