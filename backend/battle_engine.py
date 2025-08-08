"""Core algorithms for the Thronestead tactical battle system.

The full game simulation described in the design documents is extensive. For
unit testing and as a reference implementation this module provides a small
subset of that functionality:

* grid based line of sight checks using Bresenham's algorithm;
* an A* path‑finder that avoids impassable terrain and simple danger tiles.

These routines are deterministic and operate on light‑weight data classes so
that they can be tested without a running database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple
import heapq
import math


@dataclass
class TerrainTile:
    """Representation of a single map tile."""

    x: int
    y: int
    terrain_type: str = "plain"
    passable: bool = True
    move_cost: int = 1
    cover: float = 0.0
    elevation: int = 0


@dataclass
class WarUnit:
    """Simplified unit model used in path‑finding and LOS tests."""

    unit_id: str
    side: str
    x: int
    y: int
    range: int = 0
    facing: str = "N"  # Not heavily used but kept for completeness


def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Return the grid cells intersected by a line from ``(x0, y0)`` to ``(x1, y1)``.

    The implementation follows the classic Bresenham algorithm and includes
    both end points.
    """

    tiles: List[Tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    n = 1 + dx + dy
    x_inc = 1 if x1 > x0 else -1
    y_inc = 1 if y1 > y0 else -1
    error = dx - dy
    dx *= 2
    dy *= 2

    for _ in range(n):
        tiles.append((x, y))
        if error > 0:
            x += x_inc
            error -= dy
        elif error < 0:
            y += y_inc
            error += dx
        else:
            x += x_inc
            y += y_inc
            error -= dy
            error += dx
    return tiles


def line_of_sight_clear(start: Tuple[int, int], end: Tuple[int, int], tiles: dict[Tuple[int, int], TerrainTile]) -> bool:
    """Return ``True`` if LOS between ``start`` and ``end`` is unobstructed."""

    for x, y in bresenham_line(*start, *end)[1:-1]:
        tile = tiles.get((x, y))
        if tile and (tile.terrain_type in {"mountain", "forest"} or tile.elevation > 0):
            return False
    return True


def compute_visibility(observer: WarUnit, units: Sequence[WarUnit], tiles: dict[Tuple[int, int], TerrainTile], max_range: int) -> List[WarUnit]:
    """Return enemy units visible to ``observer``.

    Visibility is blocked by mountains/forests and limited by ``max_range``.
    """

    visible: List[WarUnit] = []
    for target in units:
        if target.side == observer.side:
            continue
        dx = target.x - observer.x
        dy = target.y - observer.y
        distance = math.hypot(dx, dy)
        if distance > max_range:
            continue
        if line_of_sight_clear((observer.x, observer.y), (target.x, target.y), tiles):
            visible.append(target)
    return visible


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(node: Tuple[int, int]) -> Iterable[Tuple[int, int]]:
    x, y = node
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yield x + dx, y + dy


def compute_path(start: Tuple[int, int], goal: Tuple[int, int], tiles: dict[Tuple[int, int], TerrainTile], danger: Iterable[Tuple[int, int]] = ()) -> List[TerrainTile] | None:
    """Compute a path using A* search avoiding impassable or dangerous tiles."""

    danger_set = set(danger)
    open_set: list[tuple[float, Tuple[int, int]]] = [(0, start)]
    came_from: dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return [tiles[(x, y)] for x, y in path]
        for neighbor in get_neighbors(current):
            tile = tiles.get(neighbor)
            if not tile or not tile.passable or neighbor in danger_set:
                continue
            tentative_g = g_score[current] + tile.move_cost
            if tentative_g < g_score.get(neighbor, math.inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return None
