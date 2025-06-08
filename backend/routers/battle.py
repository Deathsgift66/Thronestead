from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models

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

def _load_war_from_db(war_id: int, db: Session) -> WarState:
    db_war = db.query(models.WarsTactical).filter(models.WarsTactical.war_id == war_id).first()
    if not db_war:
        raise HTTPException(status_code=404, detail="War not found")
    terrain_row = db.query(models.TerrainMap).filter(models.TerrainMap.war_id == war_id).first()
    terrain = terrain_row.tile_map if terrain_row else TerrainGenerator().generate()
    war = WarState(war_id=db_war.war_id, tick=db_war.battle_tick, castle_hp=db_war.castle_hp, terrain=terrain)
    movements = db.query(models.UnitMovement).filter(models.UnitMovement.war_id == war_id).all()
    for mov in movements:
        war.units.append(Unit(
            unit_id=mov.movement_id,
            kingdom_id=mov.kingdom_id,
            unit_type=mov.unit_type,
            quantity=mov.quantity,
            x=mov.position_x,
            y=mov.position_y,
            stance=mov.stance,
        ))
    return war


@router.post("/api/start-battle/{war_id}")
def start_battle(war_id: int, db: Session = Depends(get_db)):
    war = _load_war_from_db(war_id, db)
    _manager.start_war(war)
    return {"status": "started", "war_id": war_id}


@router.post("/api/run-tick/{war_id}")
def run_tick(war_id: int, db: Session = Depends(get_db)):
    war = _manager.get_war(war_id)
    if not war:
        raise HTTPException(status_code=404, detail="war not active")
    logs = _manager.tick_handler.run_tick(war)
    db_war = db.query(models.WarsTactical).filter(models.WarsTactical.war_id == war_id).first()
    if db_war:
        db_war.castle_hp = war.castle_hp
        db_war.battle_tick = war.tick
    for log in logs:
        db_log = models.CombatLog(
            war_id=war_id,
            tick_number=war.tick,
            event_type=log.get("event"),
            attacker_unit_id=log.get("attacker_id"),
            defender_unit_id=log.get("defender_id"),
            position_x=log.get("pos", (None, None))[0] if isinstance(log.get("pos"), tuple) else log.get("position_x"),
            position_y=log.get("pos", (None, None))[1] if isinstance(log.get("pos"), tuple) else log.get("position_y"),
            damage_dealt=log.get("damage"),
        )
        db.add(db_log)
    db.commit()
    _manager.get_logs(war_id).extend(logs)
    return {"tick": war.tick, "castle_hp": war.castle_hp, "logs": logs}


@router.get("/api/battle-resolution/{war_id}")
def battle_resolution(war_id: int, db: Session = Depends(get_db)):
    res = db.query(models.BattleResolutionLog).filter(models.BattleResolutionLog.war_id == war_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="resolution not found")
    return {
        "winner_side": res.winner_side,
        "total_ticks": res.total_ticks,
        "attacker_casualties": res.attacker_casualties,
        "defender_casualties": res.defender_casualties,
    }


@router.get("/api/battle-replay/{war_id}")
def battle_replay(war_id: int, db: Session = Depends(get_db)):
    logs = db.query(models.CombatLog).filter(models.CombatLog.war_id == war_id).order_by(models.CombatLog.tick_number).all()
    return {"logs": [
        {
            "tick": l.tick_number,
            "event": l.event_type,
            "attacker_unit_id": l.attacker_unit_id,
            "defender_unit_id": l.defender_unit_id,
            "position_x": l.position_x,
            "position_y": l.position_y,
            "damage_dealt": l.damage_dealt,
        }
        for l in logs
    ]}


@router.get("/api/alliance-battle-replay/{alliance_war_id}")
def alliance_battle_replay(alliance_war_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(models.AllianceWarCombatLog)
        .filter(models.AllianceWarCombatLog.alliance_war_id == alliance_war_id)
        .order_by(models.AllianceWarCombatLog.tick_number, models.AllianceWarCombatLog.combat_id)
        .all()
    )
    return {
        "logs": [
            {
                "tick": l.tick_number,
                "event": l.event_type,
                "attacker_unit_id": l.attacker_unit_id,
                "defender_unit_id": l.defender_unit_id,
                "position_x": l.position_x,
                "position_y": l.position_y,
                "damage_dealt": l.damage_dealt,
            }
            for l in logs
        ]
    }
