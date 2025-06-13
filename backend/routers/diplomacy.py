from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id

router = APIRouter(prefix="/api/diplomacy", tags=["diplomacy"])


@router.get("/alliances")
async def alliances():
    return {"alliances": []}


@router.get("/treaties")
async def treaties(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    nobles = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if nobles == 0:
        raise HTTPException(status_code=403, detail="No nobles available")
    return {"treaties": []}


@router.get("/conflicts")
async def diplomacy_conflicts():
    return {"conflicts": []}

