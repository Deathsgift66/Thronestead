# Project Name: Thronestead©
# File Name: engine.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Core engine logic for Thronestead© tactical battles.
Handles terrain generation, fog of war, unit modeling, and combat resolution.
"""

import random
import itertools
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Tuple


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
    morale: float = 100.0
    hp: int = 100
    is_support: bool = False
    is_siege: bool = False


@dataclass
class WarState:
    war_id: int
    tick: int
    castle_hp: int
    map_width: int
    map_height: int
    weather: str = "clear"
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
    """Visibility calculations taking terrain and unit vision into account."""

    def visible_tiles(
        self,
        units: List[Unit],
        terrain: List[List[TerrainType]],
        weather: str = "clear",
    ) -> Set[Tuple[int, int]]:
        """Return all tiles visible to the provided units factoring in weather."""

        visible: Set[Tuple[int, int]] = set()
        width = TerrainGenerator.WIDTH
        height = TerrainGenerator.HEIGHT

        for u in units:
            vision = 5
            tile = terrain[u.y][u.x]
            if tile == TerrainType.HILLS:
                vision += 2
            elif tile == TerrainType.FOREST:
                vision -= 1

            if weather == "fog":
                vision -= 2
            elif weather == "rain":
                vision -= 1
            vision = max(1, vision)

            min_y = max(0, u.y - vision)
            max_y = min(height - 1, u.y + vision)
            min_x = max(0, u.x - vision)
            max_x = min(width - 1, u.x + vision)

            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    visible.add((x, y))

        return visible


# --------------------------
# ⚔️ Combat Resolver
# --------------------------
class CombatResolver:
    """Handles unit-on-unit combat resolution for a battle tick."""

    def resolve(self, war: WarState, logs: List[Dict]) -> None:
        """Modify ``war`` in-place, resolving any combat interactions."""

        units_by_pos: Dict[Tuple[int, int], List[Unit]] = defaultdict(list)
        for unit in war.units:
            units_by_pos[(unit.x, unit.y)].append(unit)

        global_remove: set[Unit] = set()

        for pos, units in units_by_pos.items():
            if len(units) < 2:
                continue

            # Apply support buffs/heals before attacks
            support_units = [u for u in units if u.is_support]
            if support_units:
                for sup in support_units:
                    for ally in units:
                        if ally.kingdom_id == sup.kingdom_id and ally is not sup:
                            ally.hp = min(ally.hp + 5, 100)
                            ally.morale = min(100.0, ally.morale + 5)
                            logs.append(
                                {
                                    "event": "support",
                                    "support_id": sup.unit_id,
                                    "target_id": ally.unit_id,
                                    "pos": pos,
                                }
                            )

            # Pre-compute damage stats once per unit
            dmg_stats: Dict[Unit, tuple[int, float]] = {}
            for u in units:
                base = u.quantity * 10
                crit = 0.0
                if u.morale > 60:
                    crit = min((u.morale - 60) * 0.00125, 0.05)
                dmg_stats[u] = (base, crit)

            to_remove: set[Unit] = set()
            for attacker, defender in itertools.combinations(units, 2):
                if attacker.kingdom_id == defender.kingdom_id:
                    continue

                base_damage, crit_chance = dmg_stats[attacker]
                critical = random.random() < crit_chance
                if critical:
                    base_damage = int(base_damage * 1.5)

                damage = min(base_damage, defender.hp)
                defender.hp -= damage

                logs.append(
                    {
                        "event": "attack",
                        "attacker_id": attacker.unit_id,
                        "defender_id": defender.unit_id,
                        "pos": pos,
                        "damage": damage,
                        "critical": critical,
                    }
                )

                if defender.hp <= 0 and defender not in to_remove:
                    logs.append(
                        {
                            "event": "death",
                            "unit_id": defender.unit_id,
                            "pos": pos,
                        }
                    )
                    to_remove.add(defender)

            global_remove.update(to_remove)

        if global_remove:
            war.units = [u for u in war.units if u not in global_remove]


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
        visible = self.fog.visible_tiles(war.units, war.terrain, war.weather)
        logs.append({"event": "vision_update", "tiles": len(visible)})

        # Resolve combat
        self.combat.resolve(war, logs)

        # Siege damage phase (castle damage from siege units)
        siege_count = sum(1 for u in war.units if u.is_siege)
        if siege_count:
            damage = siege_count * 5
            war.castle_hp = max(0, war.castle_hp - damage)
            logs.append(
                {
                    "event": "siege",
                    "damage": damage,
                    "castle_hp": war.castle_hp,
                }
            )

        # Tick advance
        war.tick += 1
        return logs
