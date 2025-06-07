"""Battle system engine components."""

from .engine import (
    TerrainGenerator,
    FogOfWar,
    CombatResolver,
    BattleTickHandler,
    WarState,
    Unit,
    TerrainType,
)
from .manager import WarManager, war_manager, run_combat_tick
from .movement import (
    process_unit_movement,
    move_towards,
    terrain_movement_modifier,
    select_patrol_target,
    update_unit_position,
)
from .targeting import select_target, get_counter_multiplier

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
    "process_unit_movement",
    "move_towards",
    "terrain_movement_modifier",
    "select_patrol_target",
    "update_unit_position",
    "select_target",
    "get_counter_multiplier",
]
