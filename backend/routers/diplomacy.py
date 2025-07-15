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
from sqlalchemy import text
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
    """Return diplomatic treaties for the caller's kingdom or alliance."""
    kid = get_kingdom_id(db, user_id)

    # Determine alliance membership without raising if none exists
    alliance_id = (
        db.execute(
            text("SELECT alliance_id FROM kingdoms WHERE kingdom_id = :kid"),
            {"kid": kid},
        ).scalar()
    )

    if alliance_id:
        rows = db.execute(
            text(
                """
                SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id,
                       status, signed_at
                  FROM alliance_treaties
                 WHERE alliance_id = :aid OR partner_alliance_id = :aid
                 ORDER BY signed_at DESC
                """
            ),
            {"aid": alliance_id},
        ).fetchall()
        treaties = [
            {
                "treaty_id": r[0],
                "alliance_id": r[1],
                "treaty_type": r[2],
                "partner_alliance_id": r[3],
                "status": r[4],
                "signed_at": r[5].isoformat() if r[5] else None,
            }
            for r in rows
        ]
    else:
        rows = db.execute(
            text(
                """
                SELECT treaty_id, kingdom_id, treaty_type, partner_kingdom_id,
                       status, signed_at
                  FROM kingdom_treaties
                 WHERE kingdom_id = :kid OR partner_kingdom_id = :kid
                 ORDER BY signed_at DESC
                """
            ),
            {"kid": kid},
        ).fetchall()
        treaties = [
            {
                "treaty_id": r[0],
                "kingdom_id": r[1],
                "treaty_type": r[2],
                "partner_kingdom_id": r[3],
                "status": r[4],
                "signed_at": r[5].isoformat() if r[5] else None,
            }
            for r in rows
        ]

    return {"treaties": treaties}
