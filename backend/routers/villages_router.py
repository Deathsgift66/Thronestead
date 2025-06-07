from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id

router = APIRouter(prefix="/api/villages", tags=["villages"])

# Simple in-memory store of created villages until a dedicated table exists
kingdom_villages: dict[int, list[dict]] = {}


def get_max_villages_allowed(castle_level: int) -> int:
    """Return the number of villages allowed for the given castle level."""
    return castle_level


class VillagePayload(BaseModel):
    village_name: str
    kingdom_id: int = 1


@router.post("/create")
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
    villages.append({"village_id": village_id, "village_name": payload.village_name})

    return {"message": "Village created", "village_id": village_id}
