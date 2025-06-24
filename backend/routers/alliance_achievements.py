# Project Name: Thronestead©
# File Name: alliance_achievements.py
# Description: API routes for alliance achievements.

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.alliance_achievement_service import award_achievement, list_achievements
from services.alliance_service import get_alliance_id
from services.audit_service import log_action, log_alliance_activity

from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance/achievements", tags=["alliance_achievements"])


class AwardPayload(BaseModel):
    achievement_code: str = Field(..., min_length=1, max_length=100)


@router.get("")
def get_achievements(user_id: str = Depends(require_user_id), db: Session = Depends(get_db)) -> dict:
    """List achievements for the player's alliance."""
    alliance_id = get_alliance_id(db, user_id)
    achievements = list_achievements(db, alliance_id)
    return {"achievements": achievements}


@router.post("")
def award(payload: AwardPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)) -> dict:
    """Award an alliance achievement to the player's alliance."""
    alliance_id = get_alliance_id(db, user_id)
    points = award_achievement(db, alliance_id, payload.achievement_code)
    if points is None:
        return {"status": "exists"}

    log_action(db, user_id, "alliance_achievement_awarded", payload.achievement_code)
    log_alliance_activity(db, alliance_id, user_id, "Achievement Awarded", payload.achievement_code)

    return {"points_reward": points}
