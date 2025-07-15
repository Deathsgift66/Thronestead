"""
Project: Thronestead ©
File: quests_router.py
Role: API routes for quests router.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import QuestKingdomTracking
from services.vacation_mode_service import check_vacation_mode
from services.audit_service import log_action

from ..data import castle_progression_state
from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

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
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Complete a quest for a kingdom if requirements are met."""
    check_vacation_mode(db, payload.kingdom_id)

    req = _get_requirements(payload.quest_code)
    prog = castle_progression_state.get(
        payload.kingdom_id, {"castle_level": 0, "nobles": 0, "knights": 0}
    )

    if (
        prog["castle_level"] < req["required_castle_level"]
        or prog["nobles"] < req["required_nobles"]
        or prog["knights"] < req["required_knights"]
    ):
        raise HTTPException(status_code=403, detail="Quest requirements not met")

    log_action(db, user_id, "Quest Completed", payload.quest_code)
    return {
        "message": "Quest completed",
        "quest_code": payload.quest_code,
    }


@router.get("/active")
def get_active_quests(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return active quests for the authenticated user's kingdom."""
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
