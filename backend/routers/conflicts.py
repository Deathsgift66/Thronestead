# Project Name: Thronestead©
# File Name: conflicts.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: conflicts.py
Role: API routes for conflicts.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from .progression_router import get_kingdom_id
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/conflicts", tags=["conflicts"])

# ----------------------------
# Helper
# ----------------------------

def get_alliance_id(db: Session, user_id: str) -> int:
    """Fetch alliance ID for the user."""
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]

# ----------------------------
# Endpoints
# ----------------------------
