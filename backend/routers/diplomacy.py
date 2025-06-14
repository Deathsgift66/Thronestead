# Project Name: Kingmakers Rise©
# File Name: diplomacy.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/diplomacy", tags=["diplomacy"])


@router.get("/alliances")
def list_known_alliances():
    """
    Placeholder route to list alliances available for diplomacy.
    Expected to be replaced with a live Supabase query to public.alliances.
    """
    return {"alliances": []}


@router.get("/treaties")
async def list_treaties(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Returns available diplomatic treaties for a kingdom that has nobles.
    This will later return treaties either from:
    - alliance_treaties if part of alliance
    - kingdom-level treaties if implemented
    """
    kid = get_kingdom_id(db, user_id)
    
    nobles_count = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).scalar()

    if nobles_count == 0:
        raise HTTPException(status_code=403, detail="No nobles available for diplomacy.")

    # Placeholder for future treaty fetch (e.g., SELECT * FROM alliance_treaties WHERE ...)
    return {"treaties": []}


@router.get("/conflicts")
def list_diplomatic_conflicts():
    """
    Placeholder endpoint for conflicts relevant to diplomacy (e.g., embargoes, trade wars).
    In future, can return active non-war disputes between kingdoms or alliances.
    """
    return {"conflicts": []}
