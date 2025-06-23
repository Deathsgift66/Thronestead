# Project Name: Thronestead©
# File Name: villages_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: villages_router.py
Role: API routes for villages router.
Version: 2025-06-21
"""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..data import get_max_villages_allowed
from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/kingdom/villages", tags=["villages"])


# ----------------------------- Pydantic Schema -----------------------------
class VillagePayload(BaseModel):
    village_name: str
    village_type: str = "economic"
    kingdom_id: int | None = None


# ----------------------------- Internal Utility -----------------------------
def _fetch_villages(db: Session, kid: int):
    """Helper to fetch all villages for a given kingdom ID with metadata."""
    rows = db.execute(
        text(
            """
            SELECT v.village_id, v.village_name, v.village_type, v.created_at,
                   COUNT(b.building_id) AS building_count
            FROM kingdom_villages v
            LEFT JOIN village_buildings b ON b.village_id = v.village_id
            WHERE v.kingdom_id = :kid
            GROUP BY v.village_id
            ORDER BY v.created_at
            """
        ),
        {"kid": kid},
    ).fetchall()

    return [
        {
            "village_id": r[0],
            "village_name": r[1],
            "village_type": r[2],
            "created_at": r[3],
            "building_count": r[4],
        }
        for r in rows
    ]


# ----------------------------- API Endpoints -----------------------------


@router.get("")
async def list_villages(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    """List all villages for the authenticated player."""
    kid = get_kingdom_id(db, user_id)
    villages = _fetch_villages(db, kid)
    return {"villages": villages}


@router.post("")
def create_village(
    payload: VillagePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Create a new village if:
    - User has available slots from their castle level
    - User has at least one noble
    """
    kid = get_kingdom_id(db, user_id)

    # Check current castle level
    record = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchone()
    castle_level = record[0] if record else 1
    max_allowed = get_max_villages_allowed(castle_level)

    # Enforce cap on village creation
    existing = db.execute(
        text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if existing >= max_allowed:
        raise HTTPException(status_code=403, detail="Village limit reached")

    # Require at least one noble
    nobles = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if nobles < 1:
        raise HTTPException(status_code=403, detail="Not enough nobles")

    # Insert village
    result = db.execute(
        text(
            """
            INSERT INTO kingdom_villages (kingdom_id, village_name, village_type)
            VALUES (:kid, :name, :type)
            RETURNING village_id
            """
        ),
        {"kid": kid, "name": payload.village_name, "type": payload.village_type},
    ).fetchone()
    db.commit()
    return {"message": "Village created", "village_id": result[0]}


@router.get("/summary/{village_id}")
def get_village_summary(
    village_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return metadata, buildings, and resources for a single village."""
    kid = get_kingdom_id(db, user_id)

    # Ensure ownership
    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": village_id},
    ).fetchone()
    if not owner or owner[0] != kid:
        raise HTTPException(
            status_code=403, detail="Village does not belong to your kingdom"
        )

    # Fetch core data
    village = (
        db.execute(
            text(
                """
            SELECT village_id, village_name, village_type, created_at
            FROM kingdom_villages
            WHERE village_id = :vid
            """
            ),
            {"vid": village_id},
        )
        .mappings()
        .fetchone()
    )

    resources = (
        db.execute(
            text("SELECT * FROM village_resources WHERE village_id = :vid"),
            {"vid": village_id},
        )
        .mappings()
        .fetchone()
    )

    buildings = (
        db.execute(
            text(
                "SELECT building_id, level FROM village_buildings WHERE village_id = :vid ORDER BY building_id"
            ),
            {"vid": village_id},
        )
        .mappings()
        .fetchall()
    )

    return {
        "village": dict(village) if village else {},
        "resources": dict(resources) if resources else {},
        "buildings": [dict(b) for b in buildings],
    }


@router.get("/stream", response_class=StreamingResponse)
async def stream_villages(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    """Stream village data every 5s in Server-Sent Event format for real-time dashboards."""
    kid = get_kingdom_id(db, user_id)

    async def event_generator():
        last_update: str | None = None
        while True:
            villages = _fetch_villages(db, kid)
            if villages:
                latest = str(max(v["created_at"] for v in villages))
                if latest != last_update:
                    last_update = latest
                    data = json.dumps(villages, default=str)
                    yield f"data: {data}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
