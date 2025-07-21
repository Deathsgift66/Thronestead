# Project Name: Thronestead©
# File Name: overview.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: overview.py
Role: API routes for overview.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sqlalchemy import text

from services.progression_service import calculate_troop_slots
from services.resource_service import get_kingdom_resources
from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

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

    # Calculate total troop slots from progression bonuses
    total_slots = calculate_troop_slots(db, kingdom_id)

    # Retrieve current used slots
    row = db.execute(
        text("SELECT used_slots FROM kingdom_troop_slots WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    used_slots = int(row[0]) if row else 0

    # Fetch current resources from the database
    resources_row = get_kingdom_resources(db, kingdom_id)
    resources = {
        k: v
        for k, v in resources_row.items()
        if k not in {"kingdom_id", "created_at", "last_updated"}
    }

    return {
        "resources": resources,
        "troops": {
            "total": used_slots,
            "slots": {
                "base": total_slots,
                "used": used_slots,
                "available": max(0, total_slots - used_slots),
            },
        },
    }
