from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import QuestKingdomTracking
from .progression_router import get_user_id, get_kingdom_id
from ..data import castle_progression_state

router = APIRouter(prefix="/api/quests", tags=["quests"])


class QuestPayload(BaseModel):
    quest_code: str
    kingdom_id: int = 1


# Placeholder catalogue with requirements
def _get_requirements(code: str):
    catalogue = {
        "demo_quest": {
            "required_castle_level": 1,
            "required_nobles": 0,
            "required_knights": 0,
        }
    }
    return catalogue.get(
        code, {"required_castle_level": 0, "required_nobles": 0, "required_knights": 0}
    )


@router.post("/complete")
async def complete_quest(payload: QuestPayload):
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

    return {"message": "Quest completed", "quest_code": payload.quest_code}


@router.get("/active")
def get_active_quests(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
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
