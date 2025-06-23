# Project Name: Thronestead©
# File Name: __init__.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Battle system engine components for Thronestead©.

This package exposes all tactical combat mechanics, including:
- Fog of War
- Unit Movement and Targeting
- Combat Resolution
- Terrain Effects
- Turn-based Tick Logic
"""

# Core battle engine components
from .engine import (
    BattleTickHandler,
    CombatResolver,
    FogOfWar,
    TerrainGenerator,
    TerrainType,
    Unit,
    WarState,
)

# Combat orchestration and live war state manager
from .manager import WarManager, run_combat_tick, war_manager

# Movement logic
from .movement import (
    move_towards,
    process_unit_movement,
    select_patrol_target,
    terrain_movement_modifier,
    update_unit_position,
)

# Alternate full resolution combat (used for simulation or replays)
from .resolver_full import run_combat_tick as run_full_combat_tick

# Targeting and combat multiplier mechanics
from .targeting import get_counter_multiplier, select_target

# Vision, line of sight, and terrain-based obscurity
from .vision import process_unit_vision, terrain_vision_modifier

# Public interface for this module
__all__ = [
    "TerrainGenerator",
    "FogOfWar",
    "CombatResolver",
    "BattleTickHandler",
    "WarState",
    "Unit",
    "TerrainType",
    "WarManager",
    "war_manager",
    "run_combat_tick",
    "run_full_combat_tick",
    "process_unit_movement",
    "move_towards",
    "terrain_movement_modifier",
    "select_patrol_target",
    "update_unit_position",
    "select_target",
    "get_counter_multiplier",
    "process_unit_vision",
    "terrain_vision_modifier",
]
