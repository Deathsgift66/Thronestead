# Project Name: Thronestead©
# File Name: battle.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from backend import models
from ..security import verify_jwt_token

from ..battle_engine import (
    TerrainGenerator,
    WarState,
    Unit,
    war_manager,
)

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


@router.get("/replay/{war_id}", response_model=None)
def get_battle_replay(
    war_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return aggregated data for a completed battle."""
    war = db.query(models.WarsTactical).filter(models.WarsTactical.war_id == war_id).first()
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    units = (
        db.query(models.UnitMovement)
        .filter(models.UnitMovement.war_id == war_id)
        .all()
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
            "tick": l.tick_number,
            "message": l.notes or l.event_type,
            "attacker_unit_id": l.attacker_unit_id,
            "defender_unit_id": l.defender_unit_id,
            "position_x": l.position_x,
            "position_y": l.position_y,
            "damage_dealt": l.damage_dealt,
        }
        for l in logs
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


def battle_resolution_alt(
    war_id: int,
    user_id: str | None = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return summarized resolution info for ``war_id``."""

    war = db.query(models.WarsTactical).filter(models.WarsTactical.war_id == war_id).first()
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


@router.get("/resolution", response_model=None)
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

    war = db.query(models.WarsTactical).filter(models.WarsTactical.war_id == war_id).first()
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    terrain = db.query(models.TerrainMap).filter(models.TerrainMap.war_id == war_id).first()
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
                "tick_number": l.tick_number,
                "event_type": l.event_type,
                "damage_dealt": l.damage_dealt,
            }
            for l in logs
        ],
        "attacker_score": score.attacker_score if score else 0,
        "defender_score": score.defender_score if score else 0,
    }
