from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id
from services.kingdom_achievement_service import list_achievements

router = APIRouter(prefix="/api/kingdom/achievements", tags=["kingdom_achievements"])


@router.get("")
async def get_achievements(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Return all achievements with unlock status for the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    achievements = list_achievements(db, kid)
    return {"achievements": achievements}
