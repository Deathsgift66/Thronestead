# Project Name: Kingmakers Rise©
# File Name: resources.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any, Optional

from ..database import get_db
from backend.models import User, KingdomResources
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/resources", tags=["resources"])
logger = logging.getLogger("KingmakersRise.Resources")

# Metadata fields that should never be exposed to the client
METADATA_FIELDS = {"kingdom_id", "created_at", "last_updated"}


def _fetch_supabase_resources(user_id: str) -> Optional[Dict[str, Any]]:
    """Return kingdom resources via Supabase or ``None`` on failure."""
    try:
        supabase = get_supabase_client()
    except RuntimeError:
        return None

    try:
        kid_resp = (
            supabase.table("kingdoms")
            .select("kingdom_id")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if getattr(kid_resp, "status_code", 200) >= 400:
            logger.error("Supabase error fetching kingdom: %s", getattr(kid_resp, "error", "unknown"))
            return None

        kid_data = getattr(kid_resp, "data", kid_resp) or {}
        kid = kid_data.get("kingdom_id")
        if not kid:
            return None

        res_resp = (
            supabase.table("kingdom_resources")
            .select("*")
            .eq("kingdom_id", kid)
            .single()
            .execute()
        )
        if getattr(res_resp, "status_code", 200) >= 400:
            logger.error("Supabase error fetching resources: %s", getattr(res_resp, "error", "unknown"))
            return None

        row = getattr(res_resp, "data", res_resp) or {}
        if not row:
            return None

        return {k: v for k, v in row.items() if k not in METADATA_FIELDS}
    except Exception:
        logger.exception("Error retrieving resources from Supabase")
        return None


@router.get("")
def get_resources(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Return the player's kingdom resource ledger.

    - Attempts Supabase if available for real-time reads
    - Falls back to SQLAlchemy if Supabase fails or is misconfigured
    - Removes metadata fields from the returned payload
    """
    # Attempt Supabase first for real-time reads
    resources = _fetch_supabase_resources(user_id)
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
