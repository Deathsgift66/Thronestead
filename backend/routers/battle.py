# Project Name: Kingmakers Rise©
# File Name: battle.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from backend import models
from ..security import verify_jwt_token

from ..battle_engine import (
    TerrainGenerator,
    WarState,
    Unit,
    war_manager,
)

router = APIRouter(tags=["battle"])

# In-memory store for demo purposes
_manager = war_manager


def _load_war_from_db(war_id: int, db: Session) -> WarState:
    db_war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not db_war:
        raise HTTPException(status_code=404, detail="War not found")
    terrain_row = (
        db.query(models.TerrainMap).filter(models.TerrainMap.war_id == war_id).first()
    )
    terrain = terrain_row.tile_map if terrain_row else TerrainGenerator().generate()
    width = terrain_row.map_width if terrain_row else TerrainGenerator.WIDTH
    height = terrain_row.map_height if terrain_row else TerrainGenerator.HEIGHT
    war = WarState(
        war_id=db_war.war_id,
        tick=db_war.battle_tick,
        castle_hp=db_war.castle_hp,
        map_width=width,
        map_height=height,
        terrain=terrain,
    )
    movements = (
        db.query(models.UnitMovement).filter(models.UnitMovement.war_id == war_id).all()
    )
    for mov in movements:
        war.units.append(
            Unit(
                unit_id=mov.movement_id,
                kingdom_id=mov.kingdom_id,
                unit_type=mov.unit_type,
                quantity=mov.quantity,
                x=mov.position_x,
                y=mov.position_y,
                stance=mov.stance,
            )
        )
    return war


@router.post("/api/start-battle/{war_id}")
def start_battle(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    war = _load_war_from_db(war_id, db)
    _manager.start_war(war)
    return {"status": "started", "war_id": war_id}


@router.post("/api/battle/start/{war_id}")
def start_battle_alt(
    war_id: int, db: Session = Depends(get_db), user_id: str = Depends(verify_jwt_token)
):
    return start_battle(war_id, db, user_id)


@router.post("/api/run-tick/{war_id}")
def run_tick(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    war = _manager.get_war(war_id)
    if not war:
        raise HTTPException(status_code=404, detail="war not active")
    logs = _manager.tick_handler.run_tick(war)
    db_war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
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
            position_x=(
                log.get("pos", (None, None))[0]
                if isinstance(log.get("pos"), tuple)
                else log.get("position_x")
            ),
            position_y=(
                log.get("pos", (None, None))[1]
                if isinstance(log.get("pos"), tuple)
                else log.get("position_y")
            ),
            damage_dealt=log.get("damage"),
        )
        db.add(db_log)
    db.commit()
    _manager.get_logs(war_id).extend(logs)
    return {"tick": war.tick, "castle_hp": war.castle_hp, "logs": logs}


@router.post("/api/battle/next_tick")
def next_tick(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Trigger the next combat tick for a war (admin/debug)."""
    return run_tick(war_id, db)


@router.get("/api/battle/status/{war_id}")
def get_battle_status(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Return battle status with scores."""
    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="war not found")
    score = (
        db.query(models.WarScore)
        .filter(models.WarScore.war_id == war_id)
        .first()
    )
    return {
        "war_id": war.war_id,
        "phase": war.phase,
        "weather": war.weather,
        "battle_tick": war.battle_tick,
        "tick_interval_seconds": war.tick_interval_seconds,
        "castle_hp": war.castle_hp,
        "attacker_score": score.attacker_score if score else war.attacker_score,
        "defender_score": score.defender_score if score else war.defender_score,
        "is_concluded": war.is_concluded,
        "war_status": war.war_status,
    }


@router.get("/api/battle/terrain/{war_id}")
def get_battle_terrain(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Return terrain tile map for the given war."""
    terrain_row = (
        db.query(models.TerrainMap).filter(models.TerrainMap.war_id == war_id).first()
    )
    if not terrain_row:
        raise HTTPException(status_code=404, detail="terrain not found")
    return {
        "tile_map": terrain_row.tile_map,
        "map_width": terrain_row.map_width,
        "map_height": terrain_row.map_height,
    }


@router.get("/api/battle/units/{war_id}")
def get_battle_units(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Return active unit movements for the given war."""
    units = (
        db.query(models.UnitMovement).filter(models.UnitMovement.war_id == war_id).all()
    )
    return {
        "units": [
            {
                "movement_id": u.movement_id,
                "kingdom_id": u.kingdom_id,
                "unit_type": u.unit_type,
                "quantity": u.quantity,
                "position_x": u.position_x,
                "position_y": u.position_y,
            }
            for u in units
        ]
    }


class OrderPayload(BaseModel):
    movement_id: int
    position_x: int
    position_y: int


@router.post("/api/battle/orders")
def post_orders(
    payload: OrderPayload,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Update unit movement order (simplified)."""
    mov = (
        db.query(models.UnitMovement)
        .filter(models.UnitMovement.movement_id == payload.movement_id)
        .first()
    )
    if not mov:
        raise HTTPException(status_code=404, detail="movement not found")
    mov.position_x = payload.position_x
    mov.position_y = payload.position_y
    db.commit()
    return {"status": "ok"}


@router.get("/api/battle/logs/{war_id}")
def get_combat_logs(
    war_id: int,
    since: int = 0,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Return combat logs for the given war ordered by tick."""
    logs = (
        db.query(models.CombatLog)
        .filter(models.CombatLog.war_id == war_id)
        .filter(models.CombatLog.tick_number > since)
        .order_by(models.CombatLog.tick_number, models.CombatLog.combat_id)
        .all()
    )
    return {
        "combat_logs": [
            {
                "tick_number": log_entry.tick_number,
                "event_type": log_entry.event_type,
                "attacker_unit_id": log_entry.attacker_unit_id,
                "defender_unit_id": log_entry.defender_unit_id,
                "position_x": log_entry.position_x,
                "position_y": log_entry.position_y,
                "damage_dealt": log_entry.damage_dealt,
                "morale_shift": log_entry.morale_shift,
                "notes": log_entry.notes,
            }
            for log_entry in logs
        ]
    }


@router.get("/api/battle-resolution/{war_id}")
def battle_resolution(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):

    """Return post-battle summary for participants only."""
    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="war not found")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="invalid user")

    if (
        user.kingdom_id not in [war.attacker_kingdom_id, war.defender_kingdom_id]
        and not user.is_admin
    ):
        raise HTTPException(status_code=403, detail="not authorized")


    res = (
        db.query(models.BattleResolutionLog)
        .filter(models.BattleResolutionLog.war_id == war_id)
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="resolution not found")

    return {
        "winner_side": res.winner_side,
        "total_ticks": res.total_ticks,
        "attacker_casualties": res.attacker_casualties,
        "defender_casualties": res.defender_casualties,
        "loot_summary": res.loot_summary,
    }


@router.get("/api/battle/replay/{war_id}")
@router.get("/api/battle-replay/{war_id}")
def battle_replay(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Return pre-generated replay data for a finished war."""
    war = db.query(models.WarsTactical).filter(models.WarsTactical.war_id == war_id).first()
    if not war:
        raise HTTPException(status_code=404, detail="war not found")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    if user.kingdom_id not in (war.attacker_kingdom_id, war.defender_kingdom_id):
        raise HTTPException(status_code=403, detail="not authorized for this war")

    movements = (
        db.query(models.UnitMovement)
        .filter(models.UnitMovement.war_id == war_id)
        .order_by(models.UnitMovement.movement_id)
        .all()
    )

    logs = (
        db.query(models.CombatLog)
        .filter(models.CombatLog.war_id == war_id)
        .order_by(models.CombatLog.tick_number)
        .all()
    )
    res = (
        db.query(models.BattleResolutionLog)
        .filter(models.BattleResolutionLog.war_id == war_id)
        .first()
    )

    return {
        "tick_interval_seconds": war.tick_interval_seconds,
        "total_ticks": res.total_ticks if res else war.battle_tick,
        "unit_movements": [
            {
                "movement_id": m.movement_id,
                "kingdom_id": m.kingdom_id,
                "unit_type": m.unit_type,
                "position_x": m.position_x,
                "position_y": m.position_y,
                "icon": m.unit_type[0].upper(),
                "tick": 0,
            }
            for m in movements
        ],
        "combat_logs": [
            {
                "tick": log_entry.tick_number,
                "message": log_entry.notes or log_entry.event_type,
                "attacker_unit_id": log_entry.attacker_unit_id,
                "defender_unit_id": log_entry.defender_unit_id,
                "position_x": log_entry.position_x,
                "position_y": log_entry.position_y,
                "damage_dealt": log_entry.damage_dealt,
            }
            for log_entry in logs
        ],
        "battle_resolution": {
            "status": res.winner_side if res else "pending",
            "winner": res.winner_side,
            "casualties": (res.attacker_casualties + res.defender_casualties) if res else 0,
            "castle_damage": 0,
            "loot": res.loot_summary if res else {},
        },
    }


@router.get("/api/alliance-battle-replay/{alliance_war_id}")
def alliance_battle_replay(
    alliance_war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    logs = (
        db.query(models.AllianceWarCombatLog)
        .filter(models.AllianceWarCombatLog.alliance_war_id == alliance_war_id)
        .order_by(
            models.AllianceWarCombatLog.tick_number,
            models.AllianceWarCombatLog.combat_id,
        )
        .all()
    )
    return {
        "logs": [
            {
                "tick": log_entry.tick_number,
                "event": log_entry.event_type,
                "attacker_unit_id": log_entry.attacker_unit_id,
                "defender_unit_id": log_entry.defender_unit_id,
                "position_x": log_entry.position_x,
                "position_y": log_entry.position_y,
                "damage_dealt": log_entry.damage_dealt,
            }
            for log_entry in logs
        ]
    }


@router.get("/api/battle/scoreboard/{war_id}")
def get_battle_scoreboard(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    score = (
        db.query(models.WarScore)
        .filter(models.WarScore.war_id == war_id)
        .first()
    )
    if not score:
        raise HTTPException(status_code=404, detail="score not found")
    return {
        "war_id": score.war_id,
        "attacker_score": score.attacker_score,
        "defender_score": score.defender_score,
        "victor": score.victor,
    }


def _aggregate_war_summary(db: Session, war_id: int) -> dict:
    """Return aggregated kill and morale totals for a war."""

    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        return {}

    units = (
        db.query(models.UnitMovement.movement_id, models.UnitMovement.kingdom_id)
        .filter(models.UnitMovement.war_id == war_id)
        .all()
    )
    owner_by_unit = {u.movement_id: u.kingdom_id for u in units}

    logs = (
        db.query(models.CombatLog)
        .filter(models.CombatLog.war_id == war_id)
        .all()
    )

    att_id = war.attacker_kingdom_id
    def_id = war.defender_kingdom_id

    summary = {
        "attacker_kills": 0,
        "defender_kills": 0,
        "attacker_morale": 0,
        "defender_morale": 0,
    }

    for log in logs:
        kid = owner_by_unit.get(log.defender_unit_id)
        if kid == att_id:
            summary["attacker_kills"] += log.damage_dealt or 0
            summary["attacker_morale"] += log.morale_shift or 0
        elif kid == def_id:
            summary["defender_kills"] += log.damage_dealt or 0
            summary["defender_morale"] += log.morale_shift or 0

    return summary


@router.get("/api/battle/summary/{war_id}")
def get_battle_summary(
    war_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Return simple aggregated results for a war."""

    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="war not found")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="invalid user")

    if (
        user.kingdom_id not in [war.attacker_kingdom_id, war.defender_kingdom_id]
        and not user.is_admin
    ):
        raise HTTPException(status_code=403, detail="not authorized")

    return _aggregate_war_summary(db, war_id)
