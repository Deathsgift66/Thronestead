# Project Name: Thronestead©
# File Name: navigation_ui_consolidated.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""
Consolidated entry point exposing all battle engine utilities for the
Navigation/UI layer.

This module simply re-exports classes and functions from ``backend.battle_engine``
so that frontend oriented code can import everything from a single location::

    from backend.navigation_ui_consolidated import BattleTickHandler, war_manager

All underlying modules remain unchanged; this file acts as a convenience wrapper.
"""

from .battle_engine.engine import (
    TerrainGenerator,
    TerrainType,
    Unit,
    WarState,
    FogOfWar,
    CombatResolver,
    BattleTickHandler,
)
from .battle_engine.manager import WarManager, war_manager, run_combat_tick
from .battle_engine.movement import (
    process_unit_movement,
    move_towards,
    terrain_movement_modifier,
    select_patrol_target,
    update_unit_position,
    advance_along_path,
    persist_movement_path,
)
from .battle_engine.targeting import select_target, get_counter_multiplier
from .battle_engine.vision import process_unit_vision, terrain_vision_modifier
from .battle_engine.resolver_full import (
    process_unit_combat,
    run_combat_tick as run_full_combat_tick,
    process_kingdom_war_tick,
    process_alliance_war_tick,
    update_alliance_war_score,
    check_victory_condition_kingdom,
    check_victory_condition_alliance,
    determine_victor,
    determine_victor_alliance,
    calculate_kingdom_war_casualties,
    calculate_alliance_war_casualties,
)

__all__ = [
    "TerrainGenerator",
    "TerrainType",
    "Unit",
    "WarState",
    "FogOfWar",
    "CombatResolver",
    "BattleTickHandler",
    "WarManager",
    "war_manager",
    "run_combat_tick",
    "run_full_combat_tick",
    "process_unit_movement",
    "move_towards",
    "terrain_movement_modifier",
    "select_patrol_target",
    "update_unit_position",
    "advance_along_path",
    "persist_movement_path",
    "select_target",
    "get_counter_multiplier",
    "process_unit_vision",
    "terrain_vision_modifier",
    "process_unit_combat",
    "process_kingdom_war_tick",
    "process_alliance_war_tick",
    "update_alliance_war_score",
    "check_victory_condition_kingdom",
    "check_victory_condition_alliance",
    "determine_victor",
    "determine_victor_alliance",
    "calculate_kingdom_war_casualties",
    "calculate_alliance_war_casualties",
]
