# Project Name: Kingmakers Rise©
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


# -------------------------------
# Begin construction of new building
# -------------------------------
@router.post("/construct")
def construct_build(
    payload: BuildingActionPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kingdom_id = get_kingdom_id(db, user_id)

    # Validate ownership
    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": payload.village_id}
    ).fetchone()
    if not owner or owner[0] != kingdom_id:
        raise HTTPException(403, "Village does not belong to your kingdom")

    # Fetch build time
    result = db.execute(
        text("SELECT build_time_seconds FROM building_catalogue WHERE building_id = :bid"),
        {"bid": payload.building_id}
    ).fetchone()
    if not result:
        raise HTTPException(404, "Building not found")
    build_time = result[0]

    db.execute(
        text("""
            INSERT INTO village_buildings (
                village_id, building_id, level,
                construction_started_at, construction_ends_at,
                is_under_construction, constructed_by, construction_status
            ) VALUES (
                :vid, :bid, 1, now(), now() + make_interval(secs := :secs),
                true, :uid, 'under_construction'
            )
            ON CONFLICT (village_id, building_id) DO UPDATE
              SET construction_started_at = now(),
                  construction_ends_at = now() + make_interval(secs := :secs),
                  is_under_construction = true,
                  constructed_by = :uid,
                  construction_status = 'under_construction'
        """),
        {"vid": payload.village_id, "bid": payload.building_id, "secs": build_time, "uid": user_id}
    )

    log_action(db, user_id, "start_build", f"{payload.village_id}:{payload.building_id}")
    db.commit()
    return {"message": "Construction started"}


# -------------------------------
# Upgrade an existing building
# -------------------------------
@router.post("/upgrade")
def upgrade_build(
    payload: BuildingActionPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kingdom_id = get_kingdom_id(db, user_id)

    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": payload.village_id}
    ).fetchone()
    if not owner or owner[0] != kingdom_id:
        raise HTTPException(403, "Village does not belong to your kingdom")

    existing = db.execute(
        text("SELECT level, is_under_construction FROM village_buildings WHERE village_id = :vid AND building_id = :bid"),
        {"vid": payload.village_id, "bid": payload.building_id}
    ).fetchone()

    if not existing:
        raise HTTPException(404, "Building not constructed yet")
    if existing[1]:
        raise HTTPException(400, "Upgrade already in progress")

    build_time = db.execute(
        text("SELECT build_time_seconds FROM building_catalogue WHERE building_id = :bid"),
        {"bid": payload.building_id}
    ).fetchone()[0]

    db.execute(
        text("""
            UPDATE village_buildings
               SET construction_started_at = now(),
                   construction_ends_at = now() + make_interval(secs := :secs),
                   is_under_construction = true,
                   construction_status = 'under_construction',
                   constructed_by = :uid
             WHERE village_id = :vid AND building_id = :bid
        """),
        {"vid": payload.village_id, "bid": payload.building_id, "secs": build_time, "uid": user_id}
    )

    log_action(db, user_id, "upgrade_build", f"{payload.village_id}:{payload.building_id}")
    db.commit()
    return {"message": "Upgrade started", "level": existing[0] + 1}


# -------------------------------
# Cancel active construction
# -------------------------------
@router.post("/cancel")
def cancel_build(
    payload: BuildingActionPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kingdom_id = get_kingdom_id(db, user_id)

    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": payload.village_id}
    ).fetchone()
    if not owner or owner[0] != kingdom_id:
        raise HTTPException(403, "Village does not belong to your kingdom")

    db.execute(
        text("""
            UPDATE village_buildings
               SET is_under_construction = false,
                   construction_status = 'idle',
                   construction_started_at = NULL,
                   construction_ends_at = NULL
             WHERE village_id = :vid AND building_id = :bid
        """),
        {"vid": payload.village_id, "bid": payload.building_id}
    )

    log_action(db, user_id, "cancel_build", f"{payload.village_id}:{payload.building_id}")
    db.commit()
    return {"message": "Construction cancelled"}


# -------------------------------
# Get building definition info
# -------------------------------
@router.get("/info/{building_id}")
def get_building_info(
    building_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT * FROM building_catalogue WHERE building_id = :bid"),
        {"bid": building_id}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(404, "Building not found")
    return {"building": dict(row)}


# -------------------------------
# Reset a building back to level 0
# -------------------------------
@router.post("/reset")
def reset_build(
    payload: BuildingActionPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kingdom_id = get_kingdom_id(db, user_id)

    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": payload.village_id}
    ).fetchone()
    if not owner or owner[0] != kingdom_id:
        raise HTTPException(403, "Village does not belong to your kingdom")

    db.execute(
        text("""
            UPDATE village_buildings
               SET level = 0,
                   is_under_construction = false,
                   construction_status = 'idle',
                   construction_started_at = NULL,
                   construction_ends_at = NULL
             WHERE village_id = :vid AND building_id = :bid
        """),
        {"vid": payload.village_id, "bid": payload.building_id}
    )

    log_action(db, user_id, "reset_build", f"{payload.village_id}:{payload.building_id}")
    db.commit()
    return {"message": "Building reset"}
