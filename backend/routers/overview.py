# Project Name: Thronestead©
# File Name: overview.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..security import require_user_id
from .progression_router import get_kingdom_id
from ..database import get_db
from ..data import military_state
from services.resource_service import get_kingdom_resources

router = APIRouter(prefix="/api/overview", tags=["overview"])


@router.get("/")
def get_overview(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Return a summary overview of the current kingdom's:
    - resource totals
    - troop slot usage
    """
    try:
        kingdom_id = get_kingdom_id(db, user_id)
    except HTTPException as e:
        raise e

    # Fetch military state or use defaults if kingdom not initialized yet
    state = military_state.get(
        kingdom_id,
        {
            "base_slots": 20,
            "used_slots": 0,
            "morale": 100,
            "queue": [],
            "history": [],
        },
    )

    # Fetch current resources from the database
    resources_row = get_kingdom_resources(db, kingdom_id)
    resources = {
        k: v
        for k, v in resources_row.items()
        if k not in {"kingdom_id", "created_at", "last_updated"}
    }

    base_slots = state.get("base_slots", 20)
    used_slots = state.get("used_slots", 0)

    return {
        "resources": resources,
        "troops": {
            "total": used_slots,
            "slots": {
                "base": base_slots,
                "used": used_slots,
                "available": max(0, base_slots - used_slots),
            },
        },
    }
