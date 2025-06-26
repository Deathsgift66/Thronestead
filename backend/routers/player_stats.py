"""
Project: Thronestead ©
File: player_stats.py
Role: API routes for player statistics.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.vip_status_service import get_vip_status, is_vip_active

from ..database import get_db
from ..rate_limiter import limiter
from ..security import require_user_id

router = APIRouter(prefix="/api/player-stats", tags=["player_stats"])


# -------------------------------------------------------------
# Helper: Verify VIP2 Access
# -------------------------------------------------------------

def _require_vip2(db: Session, user_id: str) -> None:
    """Raise 403 if the user does not have an active VIP level 2 or higher."""
    record = get_vip_status(db, user_id)
    if not record or record.get("vip_level", 0) < 2 or not is_vip_active(record):
        raise HTTPException(status_code=403, detail="VIP2 required")


# -------------------------------------------------------------
# 📊 Endpoints
# -------------------------------------------------------------


@router.get("/scores/{kingdom_id}")
@limiter.limit("60/minute")
def kingdom_scores(
    request: Request,
    kingdom_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Return economy, military, diplomacy and prestige scores for a kingdom."""
    _require_vip2(db, user_id)

    row = db.execute(
        text(
            "SELECT prestige_score, economy_score, military_score, diplomacy_score "
            "FROM kingdoms WHERE kingdom_id = :kid"
        ),
        {"kid": kingdom_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Kingdom not found")

    return {
        "kingdom_id": kingdom_id,
        "prestige_score": row[0],
        "economy_score": row[1],
        "military_score": row[2],
        "diplomacy_score": row[3],
    }


@router.get("/army/{kingdom_id}")
@limiter.limit("60/minute")
def army_composition(
    request: Request,
    kingdom_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Return a list of troop stacks for the specified kingdom."""
    _require_vip2(db, user_id)

    rows = db.execute(
        text(
            "SELECT unit_type, unit_level, quantity "
            "FROM kingdom_troops WHERE kingdom_id = :kid "
            "ORDER BY unit_type, unit_level"
        ),
        {"kid": kingdom_id},
    ).fetchall()

    army = [
        {"unit_type": r[0], "unit_level": r[1], "quantity": r[2]} for r in rows
    ]
    return {"kingdom_id": kingdom_id, "army": army}
