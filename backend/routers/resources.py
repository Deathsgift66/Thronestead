# Project Name: Thronestead©
# File Name: resources.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: resources.py
Role: API routes for resources.
Version: 2025-06-21
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models import KingdomResources, User
from services.resource_service import METADATA_FIELDS, fetch_supabase_resources

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/resources", tags=["resources"])
logger = logging.getLogger("Thronestead.Resources")

# Expose shared constant from resource_service for field filtering


@router.get("")
def get_resources(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Return the player's kingdom resource ledger.

    - Attempts Supabase via :func:`fetch_supabase_resources` for real-time data.
    - Falls back to SQLAlchemy if Supabase is unavailable.
    - Removes metadata fields before returning the payload.
    """
    # Attempt Supabase first for real-time reads
    resources = fetch_supabase_resources(user_id)
    if resources is not None:
        return {"resources": resources}

    # Fallback to SQLAlchemy if Supabase fails
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.kingdom_id:
        raise HTTPException(status_code=404, detail="Kingdom not found")

    row = db.query(KingdomResources).filter_by(kingdom_id=user.kingdom_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Resources not found")

    # Build dict from model, skipping metadata fields
    resources = {
        col.name: getattr(row, col.name)
        for col in KingdomResources.__table__.columns
        if col.name not in METADATA_FIELDS
    }

    return {"resources": resources}
