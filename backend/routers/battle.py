from __future__ import annotations

from fastapi import APIRouter

from ..battle_engine import (
    BattleTickHandler,
    TerrainGenerator,
    WarState,
    Unit,
    WarManager,
    war_manager,
)

router = APIRouter(tags=["battle"])

# In-memory store for demo purposes
_manager = war_manager

def _create_demo_war(war_id: int) -> WarState:
    terrain = TerrainGenerator().generate()
    war = WarState(war_id=war_id, tick=0, castle_hp=1000, terrain=terrain)
    war.units.append(Unit(unit_id=1, kingdom_id=1, unit_type="infantry", quantity=50, x=2, y=10, stance="hold"))
    war.units.append(Unit(unit_id=2, kingdom_id=2, unit_type="infantry", quantity=50, x=57, y=10, stance="hold"))
    return war


@router.post("/api/start-battle/{war_id}")
async def start_battle(war_id: int):
    war = _create_demo_war(war_id)
    _manager.start_war(war)
    return {"status": "started", "war_id": war_id}


@router.post("/api/run-tick/{war_id}")
async def run_tick(war_id: int):
    war = _manager.get_war(war_id)
    if not war:
        return {"error": "war not found"}
    logs = _manager.tick_handler.run_tick(war)
    _manager.get_logs(war_id).extend(logs)
    return {"tick": war.tick, "castle_hp": war.castle_hp, "logs": logs}


@router.get("/api/battle-resolution/{war_id}")
async def battle_resolution(war_id: int):
    war = _manager.get_war(war_id)
    if not war:
        return {"error": "war not found"}
    return {"tick": war.tick, "castle_hp": war.castle_hp}


@router.get("/api/battle-replay/{war_id}")
async def battle_replay(war_id: int):
    return {"logs": _manager.get_logs(war_id)}
