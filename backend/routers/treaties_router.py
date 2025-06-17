# Project Name: Thronestead©
# File Name: treaties_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id
from ..data import alliance_treaties, kingdom_treaties

router = APIRouter(prefix="/api", tags=["treaties"])


class TreatyPayload(BaseModel):
    """Schema for proposing a new treaty."""
    name: str = Field(..., description="Treaty name/title")
    modifiers: Optional[dict] = Field(default_factory=dict, description="Optional modifiers for the treaty")


@router.get("/alliance/treaties", summary="List alliance treaties")
def list_alliance_treaties() -> dict:
    """
    Return the list of proposed or active treaties for the player's alliance (stubbed as alliance_id=1).
    """
    return {"treaties": alliance_treaties.get(1, [])}


@router.post("/alliance/treaties", summary="Propose an alliance treaty")
def propose_alliance_treaty(payload: TreatyPayload) -> dict:
    """
    Submit a new treaty proposal to the alliance (stubbed as alliance_id=1).
    """
    treaties = alliance_treaties.setdefault(1, [])
    treaties.append(payload.dict())
    return {"message": "Treaty proposed", "treaty": payload.dict()}


@router.get("/kingdom/treaties", summary="List kingdom treaties")
async def list_kingdom_treaties(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
) -> dict:
    """
    Return all kingdom-level treaties for the authenticated user's kingdom.
    """
    kid = get_kingdom_id(db, user_id)
    return {"treaties": kingdom_treaties.get(kid, [])}


@router.post("/kingdom/treaties", summary="Propose a kingdom treaty")
def propose_kingdom_treaty(
    payload: TreatyPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """
    Submit a new treaty proposal for the authenticated user's kingdom.
    """
    kid = get_kingdom_id(db, user_id)
    treaties = kingdom_treaties.setdefault(kid, [])
    treaties.append(payload.dict())
    return {"message": "Treaty proposed", "treaty": payload.dict()}
