# Project Name: Thronestead©
# File Name: public_kingdom.py
# Version 6.14.2025
# Developer: OpenAI Codex
"""Module docstring."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/api/kingdoms", tags=["kingdoms"])

@router.get("/public/{kingdom_id}", response_model=None)
def public_profile(kingdom_id: int, db: Session = Depends(get_db)):
    """Return public profile information for the given kingdom."""
    row = db.execute(
        text(
            """
            SELECT kingdom_name, ruler_name, motto,
                   avatar_url AS profile_picture_url,
                   prestige_score, military_score,
                   economy_score, diplomacy_score,
                   is_on_vacation
            FROM kingdoms
            WHERE kingdom_id = :kid
            """
        ),
        {"kid": kingdom_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Kingdom not found")

    count_row = db.execute(
        text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    village_count = count_row[0] if count_row else 0

    return {
        "kingdom_name": row[0],
        "ruler_name": row[1],
        "motto": row[2],
        "profile_picture_url": row[3],
        "prestige": row[4],
        "military_score": row[5],
        "economy_score": row[6],
        "diplomacy_score": row[7],
        "is_on_vacation": row[8],
        "village_count": village_count,
    }
