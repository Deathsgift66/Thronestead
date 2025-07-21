# Project Name: Thronestead©
# File Name: alliance_achievements.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""API routes for alliance achievement management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.alliance_achievement_service import award_achievement, list_achievements
from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/alliance/achievements", tags=["alliance_achievements"])


class AwardPayload(BaseModel):
    achievement_code: str


@router.get("")
def get_achievements(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)) -> dict:
    """Return the player's alliance achievements."""
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    alliance_id = int(row[0])

    achievements = list_achievements(db, alliance_id)
    return {"achievements": achievements}


@router.post("/award")
def award(
    payload: AwardPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Award an alliance achievement to the player's alliance."""
    aid_row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not aid_row or aid_row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    alliance_id = int(aid_row[0])

    exists = db.execute(
        text("SELECT 1 FROM alliances WHERE alliance_id = :aid"),
        {"aid": alliance_id},
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Alliance not found")

    points = award_achievement(db, alliance_id, payload.achievement_code)
    if points is None:
        raise HTTPException(status_code=409, detail="Achievement already awarded")
    return {"points_reward": points}
