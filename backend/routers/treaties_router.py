from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id
from ..data import alliance_treaties, kingdom_treaties

router = APIRouter(prefix="/api", tags=["treaties"])

class TreatyPayload(BaseModel):
    name: str
    modifiers: dict | None = None

@router.get("/alliance/treaties")
async def list_alliance_treaties() -> dict:
    return {"treaties": alliance_treaties.get(1, [])}

@router.post("/alliance/treaties")
async def propose_alliance_treaty(payload: TreatyPayload) -> dict:
    treaties = alliance_treaties.setdefault(1, [])
    treaties.append(payload.dict())
    return {"message": "Treaty proposed"}

@router.get("/kingdom/treaties")
async def list_kingdom_treaties(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    return {"treaties": kingdom_treaties.get(kid, [])}

@router.post("/kingdom/treaties")
async def propose_kingdom_treaty(
    payload: TreatyPayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    treaties = kingdom_treaties.setdefault(kid, [])
    treaties.append(payload.dict())
    return {"message": "Treaty proposed"}

