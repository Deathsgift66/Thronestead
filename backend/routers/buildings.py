# Project Name: Thronestead©
# File Name: buildings.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from services.audit_service import log_action
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/buildings", tags=["buildings"])


# Payload model for construction-related actions
class BuildingActionPayload(BaseModel):
    village_id: int
    building_id: int


# -------------------------------
# Get building catalogue
# -------------------------------
@router.get("/catalogue")
def get_catalogue(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM building_catalogue ORDER BY building_id")
    ).mappings().fetchall()
    return {"buildings": [dict(r) for r in rows]}


# -------------------------------
# Get buildings for a specific village
# -------------------------------
@router.get("/village/{village_id}")
def get_village_buildings(
    village_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kingdom_id = get_kingdom_id(db, user_id)

    # Verify ownership
    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": village_id}
    ).fetchone()
    if not owner or owner[0] != kingdom_id:
        raise HTTPException(403, "Village does not belong to your kingdom")

    rows = db.execute(
        text("""
            SELECT bc.*, COALESCE(vb.level, 0) AS level,
                   vb.is_under_construction, vb.construction_started_at,
                   vb.construction_ends_at
              FROM building_catalogue bc
         LEFT JOIN village_buildings vb
                ON vb.building_id = bc.building_id
               AND vb.village_id = :vid
             ORDER BY bc.building_id
        """),
        {"vid": village_id}
    ).mappings().fetchall()

    return {"buildings": [dict(r) for r in rows]}
