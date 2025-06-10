from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id
from ..data import get_max_villages_allowed

router = APIRouter(prefix="/api/kingdom/villages", tags=["villages"])

class VillagePayload(BaseModel):
    village_name: str
    village_type: str = "economic"
    kingdom_id: int | None = None


@router.get("")
async def list_villages(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """List villages for the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT village_id, village_name, village_type, is_capital, population,
                   defense_level, prosperity, created_at, last_updated
            FROM kingdom_villages
            WHERE kingdom_id = :kid
            ORDER BY created_at
            """
        ),
        {"kid": kid},
    ).fetchall()

    villages = [
        {
            "village_id": r[0],
            "village_name": r[1],
            "village_type": r[2],
            "is_capital": r[3],
            "population": r[4],
            "defense_level": r[5],
            "prosperity": r[6],
            "created_at": r[7],
            "last_updated": r[8],
        }
        for r in rows
    ]
    return {"villages": villages}


@router.post("")
async def create_village(
    payload: VillagePayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Create a new village if allowed by castle level and nobles."""
    kid = get_kingdom_id(db, user_id)

    record = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchone()
    castle_level = record[0] if record else 1
    max_allowed = get_max_villages_allowed(castle_level)

    existing = db.execute(
        text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if existing >= max_allowed:
        raise HTTPException(status_code=403, detail="Village limit reached")

    nobles = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if nobles < 1:
        raise HTTPException(status_code=403, detail="Not enough nobles")

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
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Return key details for a single village owned by the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    owner = db.execute(
        text("SELECT kingdom_id FROM kingdom_villages WHERE village_id = :vid"),
        {"vid": village_id},
    ).fetchone()
    if not owner or owner[0] != kid:
        raise HTTPException(status_code=403, detail="Village does not belong to your kingdom")

    village = db.execute(
        text(
            """
            SELECT village_id, village_name, village_type, is_capital, population,
                   defense_level, prosperity
            FROM kingdom_villages
            WHERE village_id = :vid
            """
        ),
        {"vid": village_id},
    ).mappings().fetchone()

    resources = db.execute(
        text("SELECT * FROM village_resources WHERE village_id = :vid"),
        {"vid": village_id},
    ).mappings().fetchone()

    buildings = db.execute(
        text(
            "SELECT building_id, level FROM village_buildings WHERE village_id = :vid ORDER BY building_id"
        ),
        {"vid": village_id},
    ).mappings().fetchall()

    return {
        "village": dict(village) if village else {},
        "resources": dict(resources) if resources else {},
        "buildings": [dict(b) for b in buildings],
    }
