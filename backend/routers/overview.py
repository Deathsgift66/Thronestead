from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .progression_router import get_user_id, get_kingdom_id
from ..database import get_db
from ..data import military_state

router = APIRouter(prefix="/api/overview", tags=["overview"])

@router.get("/")
def get_overview(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    """Return a simple overview summary for the player's kingdom."""
    try:
        kingdom_id = get_kingdom_id(db, user_id)
    except HTTPException:
        raise
    state = military_state.get(kingdom_id, {"base_slots": 20, "used_slots": 0})
    resources = {"gold": 1000, "food": 500, "wood": 300}
    return {
        "resources": resources,
        "troops": {
            "total": state.get("used_slots", 0),
            "slots": {
                "base": state.get("base_slots", 20),
                "used": state.get("used_slots", 0),
                "available": max(0, state.get("base_slots", 20) - state.get("used_slots", 0)),
            },
        },
    }
