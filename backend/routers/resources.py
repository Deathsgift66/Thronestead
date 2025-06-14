# Project Name: Kingmakers Rise©
# File Name: resources.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from backend.models import User, KingdomResources
from ..security import verify_jwt_token
from services.resource_service import fetch_supabase_resources

router = APIRouter(prefix="/api/resources", tags=["resources"])
logger = logging.getLogger("KingmakersRise.Resources")

# Metadata fields that should never be exposed to the client
METADATA_FIELDS = {"kingdom_id", "created_at", "last_updated"}


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

    row = (
        db.query(KingdomResources)
        .filter_by(kingdom_id=user.kingdom_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Resources not found")

    # Build dict from model, skipping metadata fields
    resources = {
        col.name: getattr(row, col.name)
        for col in KingdomResources.__table__.columns
        if col.name not in METADATA_FIELDS
    }

    return {"resources": resources}
