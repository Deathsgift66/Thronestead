# Project Name: Thronestead©
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
