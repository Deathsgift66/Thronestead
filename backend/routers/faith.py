# Comment
# Project Name: Thronestead©
# File Name: faith.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
"""API routes for kingdom faith progression."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.faith_service import gain_faith
from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/kingdom", tags=["faith"])


@router.get("/faith")
def get_faith(user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    """Return faith level, points, and blessings for the player's kingdom."""
    row = db.execute(text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    kid = row[0]
    rel = db.execute(
        text("SELECT faith_level, faith_points, blessings FROM kingdom_religion WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    if not rel:
        return {"faith_level": 1, "faith_points": 0, "blessings": {}}
    level, points, blessings = rel
    return {"faith_level": level, "faith_points": points, "blessings": blessings or {}}


@router.post("/faith/gain")
def gain_faith_points(
    amount: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Add faith points to the player's kingdom."""
    row = db.execute(text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    gain_faith(db, row[0], amount)
    return {"message": "faith gained"}
