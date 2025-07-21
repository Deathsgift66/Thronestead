# Project Name: Thronestead©
# File Name: buildings.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: buildings.py
Role: API routes for buildings.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/buildings", tags=["buildings"])


# Payload model for construction-related actions
class BuildingActionPayload(BaseModel):
    """Payload for building actions."""

    village_id: int
    building_id: int


# -------------------------------
# Get building catalogue
# -------------------------------
@router.get("/catalogue")
def get_catalogue(db: Session = Depends(get_db)):
    """Return the complete building catalogue."""
    rows = (
        db.execute(text("SELECT * FROM building_catalogue ORDER BY building_id"))
        .mappings()
        .fetchall()
    )
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
    """List buildings for the village owned by the requester."""
    kingdom_id = get_kingdom_id(db, user_id)

    # Verify ownership
    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": village_id},
    ).fetchone()
    if not owner or owner[0] != kingdom_id:
        raise HTTPException(403, "Village does not belong to your kingdom")

    rows = (
        db.execute(
            text(
                """
            SELECT bc.*, COALESCE(vb.level, 0) AS level,
                   vb.is_under_construction, vb.construction_started_at,
                   vb.construction_ends_at
              FROM building_catalogue bc
         LEFT JOIN village_buildings vb
                ON vb.building_id = bc.building_id
               AND vb.village_id = :vid
             ORDER BY bc.building_id
        """
            ),
            {"vid": village_id},
        )
        .mappings()
        .fetchall()
    )

    return {"buildings": [dict(r) for r in rows]}


@router.get("/info/{building_id}")
def get_building_info(
    building_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Fetch catalogue details for a specific building."""
    row = (
        db.execute(
            text("SELECT * FROM building_catalogue WHERE building_id = :bid"),
            {"bid": building_id},
        )
        .mappings()
        .fetchone()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Building not found")
    return {"building": dict(row)}


@router.post("/upgrade")
def upgrade_build(
    payload: BuildingActionPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Begin upgrading a building to the next level."""
    kid = get_kingdom_id(db, user_id)
    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": payload.village_id},
    ).fetchone()
    if not owner or owner[0] != kid:
        raise HTTPException(
            status_code=403, detail="Village does not belong to your kingdom"
        )
    seconds = db.execute(
        text(
            "SELECT build_time_seconds FROM building_catalogue WHERE building_id = :bid"
        ),
        {"bid": payload.building_id},
    ).fetchone()
    duration = seconds[0] if seconds else 3600
    from services.kingdom_building_service import upgrade_building

    upgrade_building(
        db, kid, payload.village_id, payload.building_id, user_id, duration
    )
    log_action(db, user_id, "upgrade_build", payload.dict())
    return {"message": "Upgrade started"}


@router.post("/reset")
def reset_build(
    payload: BuildingActionPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Set a village building's level back to zero."""
    kid = get_kingdom_id(db, user_id)
    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": payload.village_id},
    ).fetchone()
    if not owner or owner[0] != kid:
        raise HTTPException(
            status_code=403, detail="Village does not belong to your kingdom"
        )
    db.execute(
        text(
            "UPDATE village_buildings SET level = 0 WHERE village_id = :vid AND building_id = :bid"
        ),
        {"vid": payload.village_id, "bid": payload.building_id},
    )
    db.commit()
    log_action(db, user_id, "reset_build", payload.dict())
    return {"message": "Building reset"}
