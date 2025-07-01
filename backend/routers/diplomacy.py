# Project Name: Thronestead©
# File Name: diplomacy.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: diplomacy.py
Role: API routes for diplomacy.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models import Alliance

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/diplomacy", tags=["diplomacy"])


@router.get("/alliances")
def list_known_alliances(db: Session = Depends(get_db)):
    """Return a list of alliances available for diplomacy."""
    rows = (
        db.query(Alliance.alliance_id, Alliance.name)
        .order_by(Alliance.name)
        .limit(100)
        .all()
    )
    return {"alliances": [{"alliance_id": r.alliance_id, "name": r.name} for r in rows]}


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
    # TODO: implement returning relevant treaties once diplomacy is fully built
    get_kingdom_id(db, user_id)
    return {}
