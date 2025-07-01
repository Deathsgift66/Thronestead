# Comment
# Project Name: Thronestead©
# File Name: alliance_service.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
"""General alliance helper functions."""

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_alliance_id(db: Session, user_id: str) -> int:
    """Return the alliance_id for ``user_id`` or raise 404."""
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]
