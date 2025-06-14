# Project Name: Kingmakers Rise©
# File Name: engine.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Core engine logic for Kingmakers Rise© tactical battles.
Handles terrain generation, fog of war, unit modeling, and combat resolution.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Dict, Set

# --------------------------
# 🗺️ Terrain Definitions
# --------------------------
class TerrainType(str, Enum):
    PLAINS = "plains"
    FOREST = "forest"
    HILLS = "hills"
    RIVER = "river"
    BRIDGE = "bridge"
    WALL = "wall"


# --------------------------
# 🧱 Unit and War State Models
# --------------------------
@dataclass
class Unit:
    unit_id: int
    kingdom_id: int
    unit_type: str
    quantity: int
    x: int
    y: int
    stance: str
    morale: float = 1.0
    hp: int = 100


@dataclass
class WarState:
    war_id: int
    tick: int
    castle_hp: int
    map_width: int
    map_height: int
    units: List[Unit] = field(default_factory=list)
    terrain: List[List[TerrainType]] = field(default_factory=list)


# --------------------------
# 🗺️ Terrain Generator
# --------------------------
class TerrainGenerator:
    WIDTH = 60
    HEIGHT = 20

    TERRAIN_TYPES = [
        TerrainType.PLAINS,
        TerrainType.FOREST,
        TerrainType.HILLS,
        TerrainType.RIVER,
    ]

    def generate(self) -> List[List[TerrainType]]:
        """Generate a random 20x60 terrain map with varied terrain types."""
        return [
            [random.choice(self.TERRAIN_TYPES) for _ in range(self.WIDTH)]
            for _ in range(self.HEIGHT)
        ]


# --------------------------
# 🌫️ Fog of War
# --------------------------
class FogOfWar:
    def visible_tiles(self, units: List[Unit], terrain: List[List[TerrainType]]) -> Set[Tuple[int, int]]:
        """Calculate all tiles visible to the list of units, modified by terrain."""
        visible: Set[Tuple[int, int]] = set()

        for u in units:
            vision = 5
            if terrain[u.y][u.x] == TerrainType.HILLS:
                vision += 2
            elif terrain[u.y][u.x] == TerrainType.FOREST:
                vision -= 1

            for dy in range(-vision, vision + 1):
                for dx in range(-vision, vision + 1):
                    x = u.x + dx
                    y = u.y + dy
                    if 0 <= x < TerrainGenerator.WIDTH and 0 <= y < TerrainGenerator.HEIGHT:
                        visible.add((x, y))

        return visible


# --------------------------
# ⚔️ Combat Resolver
# --------------------------
class CombatResolver:
    def resolve(self, war: WarState, logs: List[Dict]) -> None:
        """
        Resolve all combat interactions on the map.

        Units on the same tile but from different kingdoms will fight.
        Each attack reduces defender HP. Units with zero HP are removed.
        """
        units_by_pos: Dict[Tuple[int, int], List[Unit]] = {}
        for u in war.units:
            units_by_pos.setdefault((u.x, u.y), []).append(u)

        for pos, units in units_by_pos.items():
            if len(units) < 2:
                continue

            to_remove: List[Unit] = []
            for i, attacker in enumerate(units):
                for defender in units[i + 1:]:
                    if attacker.kingdom_id == defender.kingdom_id:
                        continue

                    damage = min(attacker.quantity * 10, defender.hp)
                    defender.hp -= damage

                    logs.append({
                        "event": "attack",
                        "attacker_id": attacker.unit_id,
                        "defender_id": defender.unit_id,
                        "pos": pos,
                        "damage": damage,
                    })

                    if defender.hp <= 0 and defender not in to_remove:
                        logs.append({
                            "event": "death",
                            "unit_id": defender.unit_id,
                            "pos": pos,
                        })
                        to_remove.append(defender)

            for unit in to_remove:
                if unit in war.units:
                    war.units.remove(unit)


# --------------------------
# 🔁 Battle Tick Handler
# --------------------------
class BattleTickHandler:
    """
    Coordinates each tick of a battle:
    - Applies vision
    - Resolves combat
    - Applies siege damage
    - Increments tick counter
    """

    def __init__(self) -> None:
        self.terrain_generator = TerrainGenerator()
        self.fog = FogOfWar()
        self.combat = CombatResolver()

    def run_tick(self, war: WarState) -> List[Dict]:
        """
        Execute one tick of the battle, resolving fog, combat, and siege damage.

        Returns:
            List[Dict]: List of combat log entries from this tick.
        """
        logs: List[Dict] = []

        # Vision pass (for client rendering)
        visible = self.fog.visible_tiles(war.units, war.terrain)
        logs.append({"event": "vision_update", "tiles": len(visible)})

        # Resolve combat
        self.combat.resolve(war, logs)

        # Siege damage phase (castle damage from siege units)
        siege_units = [u for u in war.units if u.unit_type == "siege"]
        if siege_units:
            damage = len(siege_units) * 5
            war.castle_hp = max(0, war.castle_hp - damage)
            logs.append({
                "event": "siege",
                "damage": damage,
                "castle_hp": war.castle_hp,
            })

        # Tick advance
        war.tick += 1
        return logs
