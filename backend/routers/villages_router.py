from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id
from ..data import kingdom_villages, get_max_villages_allowed

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
    return {"villages": kingdom_villages.get(kid, [])}


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

    villages = kingdom_villages.setdefault(kid, [])
    if len(villages) >= max_allowed:
        raise HTTPException(status_code=403, detail="Village limit reached")

    nobles = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if nobles < 1:
        raise HTTPException(status_code=403, detail="Not enough nobles")

    village_id = len(villages) + 1
    villages.append(
        {
            "village_id": village_id,
            "village_name": payload.village_name,
            "village_type": payload.village_type,
            "created_at": datetime.utcnow().isoformat(),
            "buildings": [],
        }
    )

    return {"message": "Village created", "village_id": village_id}
