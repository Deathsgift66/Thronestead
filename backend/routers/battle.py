# Project Name: Thronestead©
# File Name: battle.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""
Project: Thronestead ©
File: battle.py
Role: API routes for battle.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend import models

from ..battle_engine import TerrainGenerator, Unit, WarState, war_manager
from ..database import get_db
from ..security import verify_jwt_token
from services.audit_service import log_action
from services.alliance_service import get_alliance_id

router = APIRouter(prefix="/api/battle", tags=["battle"])

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
        stat = (
            db.query(models.UnitStat)
            .filter(models.UnitStat.unit_type == mov.unit_type)
            .first()
        )
        war.units.append(
            Unit(
                unit_id=mov.movement_id,
                kingdom_id=mov.kingdom_id,
                unit_type=mov.unit_type,
                quantity=mov.quantity,
                x=mov.position_x,
                y=mov.position_y,
                stance=mov.stance,
                is_support=bool(stat.is_support) if stat else False,
                is_siege=bool(stat.is_siege) if stat else False,
            )
        )
    return war


@router.get("/replay/{war_id}")
def get_battle_replay(
    war_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return aggregated data for a completed battle."""
    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    units = (
        db.query(models.UnitMovement).filter(models.UnitMovement.war_id == war_id).all()
    )
    unit_movements = [
        {
            "movement_id": u.movement_id,
            "kingdom_id": u.kingdom_id,
            "unit_type": u.unit_type,
            "quantity": u.quantity,
            "position_x": u.position_x,
            "position_y": u.position_y,
            "morale": float(u.morale) if u.morale is not None else None,
            "icon": (u.unit_type or "?")[0].upper(),
            "tick": war.battle_tick,
        }
        for u in units
    ]

    logs = (
        db.query(models.CombatLog)
        .filter(models.CombatLog.war_id == war_id)
        .order_by(models.CombatLog.tick_number)
        .all()
    )
    combat_logs = [
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
    ]

    resolution = (
        db.query(models.BattleResolutionLog)
        .filter(models.BattleResolutionLog.war_id == war_id)
        .first()
    )

    battle_resolution = None
    total_ticks = war.battle_tick
    if resolution:
        battle_resolution = {
            "status": "completed",
            "winner": resolution.winner_side,
            "casualties": (resolution.attacker_casualties or 0)
            + (resolution.defender_casualties or 0),
            "castle_damage": war.castle_hp,
            "loot": resolution.loot_summary,
        }
        total_ticks = resolution.total_ticks or total_ticks

    return {
        "tick_interval_seconds": war.tick_interval_seconds,
        "total_ticks": total_ticks,
        "fog_of_war": bool(war.fog_of_war),
        "unit_movements": unit_movements,
        "combat_logs": combat_logs,
        "battle_resolution": battle_resolution,
    }


def get_battle_scoreboard(
    war_id: int,
    user_id: str | None = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return attacker/defender scores for ``war_id``."""

    row = db.query(models.WarScore).filter(models.WarScore.war_id == war_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Scoreboard not found")
    return {
        "attacker_score": row.attacker_score,
        "defender_score": row.defender_score,
        "victor": row.victor,
    }


@router.get("/status/{war_id}")
def get_battle_status(
    war_id: int,
    user_id: str | None = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return current status info for ``war_id``."""

    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    score = db.query(models.WarScore).filter(models.WarScore.war_id == war_id).first()

    return {
        "weather": war.weather,
        "phase": war.phase,
        "castle_hp": war.castle_hp,
        "battle_tick": war.battle_tick,
        "tick_interval_seconds": war.tick_interval_seconds,
        "attacker_score": score.attacker_score if score else 0,
        "defender_score": score.defender_score if score else 0,
        "fog_of_war": bool(war.fog_of_war),
    }


def battle_resolution_alt(
    war_id: int,
    user_id: str | None = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return summarized resolution info for ``war_id``."""

    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="War not found")
    meta = db.query(models.War).filter(models.War.war_id == war_id).first()

    resolution = (
        db.query(models.BattleResolutionLog)
        .filter(models.BattleResolutionLog.war_id == war_id)
        .first()
    )
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")

    score = db.query(models.WarScore).filter(models.WarScore.war_id == war_id).first()

    timeline_rows = (
        db.query(models.CombatLog)
        .filter(models.CombatLog.war_id == war_id)
        .order_by(models.CombatLog.tick_number)
        .all()
    )
    timeline = [r.notes or r.event_type for r in timeline_rows]

    participants = {
        "attacker": [meta.attacker_name] if meta and meta.attacker_name else [],
        "defender": [meta.defender_name] if meta and meta.defender_name else [],
    }

    victor_score = None
    score_breakdown = None
    if score:
        score_breakdown = {
            "attacker_score": score.attacker_score,
            "defender_score": score.defender_score,
        }
        if score.victor == "attacker":
            victor_score = score.attacker_score
        elif score.victor == "defender":
            victor_score = score.defender_score

    return {
        "winner": resolution.winner_side,
        "duration_ticks": resolution.total_ticks,
        "victor_score": victor_score,
        "score_breakdown": score_breakdown,
        "casualties": {
            "attacker": resolution.attacker_casualties,
            "defender": resolution.defender_casualties,
        },
        "loot": resolution.loot_summary,
        "timeline": timeline,
        "participants": participants,
        "stat_changes": None,
    }


@router.get("/resolution")
def battle_resolution_route(
    war_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Public API endpoint for battle resolution."""

    return battle_resolution_alt(war_id, db=db, user_id=user_id)


def get_live_battle(
    war_id: int,
    user_id: str | None = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return live battle state for ``war_id``."""

    war = (
        db.query(models.WarsTactical)
        .filter(models.WarsTactical.war_id == war_id)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    terrain = (
        db.query(models.TerrainMap).filter(models.TerrainMap.war_id == war_id).first()
    )
    movements = (
        db.query(models.UnitMovement).filter(models.UnitMovement.war_id == war_id).all()
    )
    logs = (
        db.query(models.CombatLog)
        .filter(models.CombatLog.war_id == war_id)
        .order_by(models.CombatLog.tick_number)
        .all()
    )
    score = db.query(models.WarScore).filter(models.WarScore.war_id == war_id).first()

    return {
        "war_id": war_id,
        "map_width": terrain.map_width if terrain else None,
        "map_height": terrain.map_height if terrain else None,
        "weather": war.weather,
        "phase": war.phase,
        "castle_hp": war.castle_hp,
        "battle_tick": war.battle_tick,
        "tick_interval_seconds": war.tick_interval_seconds,
        "units": [
            {
                "movement_id": m.movement_id,
                "kingdom_id": m.kingdom_id,
                "unit_type": m.unit_type,
                "quantity": m.quantity,
                "position_x": m.position_x,
                "position_y": m.position_y,
            }
            for m in movements
        ],
        "combat_logs": [
            {
                "tick_number": log_entry.tick_number,
                "event_type": log_entry.event_type,
                "damage_dealt": log_entry.damage_dealt,
            }
            for log_entry in logs
        ],
        "attacker_score": score.attacker_score if score else 0,
        "defender_score": score.defender_score if score else 0,
    }

from services.battle_history_service import fetch_history as fetch_battle_history


@router.get("/history", summary="Get recent battle history")
def get_battle_history(
    kingdom_id: int,
    limit: int = 25,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return recent completed battles for ``kingdom_id``."""
    records = fetch_battle_history(db, kingdom_id, limit)
    return {"history": records}



class DeclarePayload(BaseModel):
    """Payload for declaring an alliance battle."""

    target_alliance_id: int


@router.post("/declare")
def declare_alliance_battle(
    payload: DeclarePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Declare a new alliance battle using the caller's alliance."""

    attacker_id = get_alliance_id(db, user_id)

    row = db.execute(
        text(
            "INSERT INTO alliance_wars (attacker_alliance_id, defender_alliance_id, phase, war_status) "
            "VALUES (:att, :def, 'alert', 'pending') RETURNING alliance_war_id"
        ),
        {"att": attacker_id, "def": payload.target_alliance_id},
    ).fetchone()
    db.commit()

    log_action(
        db,
        user_id,
        "Declare War",
        f"{attacker_id} -> {payload.target_alliance_id}",
    )

    return {"success": True, "alliance_war_id": row[0]}

class OrdersPayload(BaseModel):
    """Payload for issuing a simple movement order."""

    war_id: int
    unit_id: int
    x: int
    y: int


@router.post("/orders")
def issue_orders(
    payload: OrdersPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Update target coordinates for a unit owned by the player."""

    from .progression_router import get_kingdom_id

    kingdom_id = get_kingdom_id(db, user_id)

    unit = (
        db.query(models.UnitMovement)
        .filter(
            models.UnitMovement.movement_id == payload.unit_id,
            models.UnitMovement.war_id == payload.war_id,
        )
        .first()
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.kingdom_id != kingdom_id:
        raise HTTPException(status_code=403, detail="Cannot command this unit")

    unit.target_tile_x = payload.x
    unit.target_tile_y = payload.y
    unit.issued_by = user_id
    db.commit()

    return {"status": "updated"}

@router.get("/wars")
def list_alliance_wars(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return active wars for the user's alliance."""
    aid = get_alliance_id(db, user_id)
    rows = (
        db.execute(
            text(
                """
                SELECT w.alliance_war_id,
                       w.phase,
                       w.attacker_alliance_id,
                       w.defender_alliance_id,
                       s.attacker_score,
                       s.defender_score,
                       CASE WHEN w.attacker_alliance_id = :aid THEN w.defender_alliance_id
                            ELSE w.attacker_alliance_id END AS enemy_id
                  FROM alliance_wars w
                  LEFT JOIN alliance_war_scores s
                    ON s.alliance_war_id = w.alliance_war_id
                 WHERE (w.attacker_alliance_id = :aid OR w.defender_alliance_id = :aid)
                   AND w.war_status = 'active'
                 ORDER BY w.start_date DESC
                """
            ),
            {"aid": aid},
        )
        .mappings()
        .fetchall()
    )

    wars = []
    for r in rows:
        enemy_name_row = db.execute(
            text("SELECT name FROM alliances WHERE alliance_id = :aid"),
            {"aid": r["enemy_id"]},
        ).fetchone()
        enemy_name = enemy_name_row[0] if enemy_name_row else str(r["enemy_id"])
        if r["attacker_alliance_id"] == aid:
            our_score = r["attacker_score"] or 0
            their_score = r["defender_score"] or 0
        else:
            our_score = r["defender_score"] or 0
            their_score = r["attacker_score"] or 0
        wars.append(
            {
                "alliance_war_id": r["alliance_war_id"],
                "enemy_name": enemy_name,
                "phase": r["phase"],
                "our_score": our_score,
                "their_score": their_score,
            }
        )
    return wars


