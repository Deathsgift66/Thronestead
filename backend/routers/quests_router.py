# Project Name: Kingmakers Rise©
# File Name: quests_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import QuestKingdomTracking
from ..security import require_user_id
from .progression_router import get_kingdom_id
from ..data import castle_progression_state
from services.vacation_mode_service import check_vacation_mode

router = APIRouter(prefix="/api/quests", tags=["quests"])


class QuestPayload(BaseModel):
    quest_code: str
    kingdom_id: int = 1


# Placeholder quest requirement catalogue
def _get_requirements(code: str):
    # You can later move this to Supabase or an external static quest registry
    catalogue = {
        "demo_quest": {
            "required_castle_level": 1,
            "required_nobles": 0,
            "required_knights": 0,
        },
        # Add more quests here...
    }
    return catalogue.get(
        code,
        {
            "required_castle_level": 0,
            "required_nobles": 0,
            "required_knights": 0,
        },
    )


@router.post("/complete")
def complete_quest(
    payload: QuestPayload,
    db: Session = Depends(get_db),
):
    """
    Complete a quest for a specific kingdom if all requirements are met.
    Requirements: castle level, nobles, knights. Vacation mode blocks completion.
    """
    check_vacation_mode(db, payload.kingdom_id)

    # Pull requirement definitions and current progression state
    req = _get_requirements(payload.quest_code)
    prog = castle_progression_state.get(
        payload.kingdom_id, {"castle_level": 0, "nobles": 0, "knights": 0}
    )

    # Validate quest unlock conditions
    if (
        prog["castle_level"] < req["required_castle_level"]
        or prog["nobles"] < req["required_nobles"]
        or prog["knights"] < req["required_knights"]
    ):
        raise HTTPException(status_code=403, detail="Quest requirements not met")

    # Success response
    return {
        "message": "Quest completed",
        "quest_code": payload.quest_code,
    }


@router.get("/active")
def get_active_quests(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Return a list of currently active quests for the authenticated user's kingdom.
    """
    kid = get_kingdom_id(db, user_id)

    rows = (
        db.query(QuestKingdomTracking)
        .filter(QuestKingdomTracking.kingdom_id == kid)
        .filter(QuestKingdomTracking.status == "active")
        .all()
    )

    return [
        {
            "quest_code": r.quest_code,
            "status": r.status,
            "progress": r.progress,
            "ends_at": r.ends_at,
            "started_at": r.started_at,
        }
        for r in rows
    ]
