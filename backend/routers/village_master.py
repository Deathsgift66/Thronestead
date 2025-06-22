# Project Name: Thronestead©
# File Name: village_master.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: village_master.py
Role: API routes for village master.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

# Define the router with appropriate tags and prefix
router = APIRouter(prefix="/api/village-master", tags=["village_master"])


@router.get("/overview", summary="Village Overview", response_model=None)
def village_overview(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Return an overview of all villages for the authenticated user's kingdom.

    Includes:
    - Village ID
    - Village Name
    - Number of buildings
    - Total level of all buildings
    """
    # Resolve the user's kingdom ID from the security layer
    kid = get_kingdom_id(db, user_id)

    # Execute SQL to gather aggregated building data per village
    rows = db.execute(
        text(
            """
            SELECT v.village_id, 
                   v.village_name,
                   COUNT(b.building_id) AS building_count,
                   COALESCE(SUM(b.level), 0) AS total_level
            FROM kingdom_villages v
            LEFT JOIN village_buildings b ON b.village_id = v.village_id
            WHERE v.kingdom_id = :kid
            GROUP BY v.village_id
            ORDER BY v.created_at
            """
        ),
        {"kid": kid},
    ).fetchall()

    # Transform raw SQL results into a clean JSON-compatible structure
    return {
        "overview": [
            {
                "village_id": r[0],
                "village_name": r[1],
                "building_count": int(r[2]),
                "total_level": int(r[3]),
            }
            for r in rows
        ]
    }


@router.post("/bulk_upgrade", summary="Bulk upgrade all village buildings", response_model=None)
def bulk_upgrade_all(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Increase the level of every building in the player's villages."""
    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            """
            UPDATE village_buildings vb
               SET level = level + 1,
                   last_updated = now()
              FROM kingdom_villages kv
             WHERE kv.village_id = vb.village_id
               AND kv.kingdom_id = :kid
            """
        ),
        {"kid": kid},
    )
    db.commit()
    return {"status": "upgraded"}


@router.post("/bulk_queue_training", summary="Queue troops in all villages", response_model=None)
def bulk_queue_training(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Queue a default training order in every village."""
    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            """
            INSERT INTO training_queue (kingdom_id, unit_id, unit_name, quantity,
                                       training_ends_at, started_at, status,
                                       training_speed_modifier,
                                       modifiers_applied, initiated_by, priority)
            SELECT :kid, 1, 'Militia', 10,
                   now() + interval '60 seconds', now(), 'queued',
                   1, '{}', :uid, 1
              FROM kingdom_villages kv
             WHERE kv.kingdom_id = :kid
            """
        ),
        {"kid": kid, "uid": user_id},
    )
    db.commit()
    return {"status": "queued"}


@router.post("/bulk_harvest", summary="Harvest all village resources", response_model=None)
def bulk_harvest(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Harvest accumulated resources in all villages."""
    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            """
            UPDATE village_resources vr
               SET last_harvested = now()
              FROM kingdom_villages kv
             WHERE kv.village_id = vr.village_id
               AND kv.kingdom_id = :kid
            """
        ),
        {"kid": kid},
    )
    db.commit()
    return {"status": "harvested"}
