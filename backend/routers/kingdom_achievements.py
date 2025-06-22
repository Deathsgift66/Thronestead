# Project Name: Thronestead©
# File Name: kingdom_achievements.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: kingdom_achievements.py
Role: API routes for kingdom achievements.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id
from services.kingdom_achievement_service import list_achievements

# Set up router
router = APIRouter(
    prefix="/api/kingdom/achievements",
    tags=["kingdom_achievements"]
)


@router.get("", response_model=None)
async def get_achievements(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    ✅ Endpoint: Get Kingdom Achievements
    
    Returns a list of all available achievements and whether they’ve been unlocked
    by the authenticated user's kingdom.

    Returns:
        {
            "achievements": [
                {
                    "achievement_code": "first_quest",
                    "name": "First Steps",
                    "description": "Complete your first kingdom quest.",
                    "category": "progression",
                    "points_reward": 10,
                    "badge_icon_url": "url",
                    "is_hidden": false,
                    "is_repeatable": false,
                    "unlocked": true,
                    "awarded_at": "2025-06-01T12:00:00Z"
                },
                ...
            ]
        }
    """
    # Resolve kingdom ID linked to the user
    kingdom_id = get_kingdom_id(db, user_id)

    # Fetch full achievement list with unlock status
    achievements = list_achievements(db, kingdom_id)

    return {"achievements": achievements}
