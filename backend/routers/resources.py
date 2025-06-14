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
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/resources", tags=["resources"])
logger = logging.getLogger("KingmakersRise.Resources")


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
    # Attempt Supabase fetch
    try:
        supabase = get_supabase_client()
    except RuntimeError:
        supabase = None

    if supabase:
        try:
            # Fetch the kingdom ID for the given user
            kingdom_res = (
                supabase.table("kingdoms")
                .select("kingdom_id")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            if getattr(kingdom_res, "status_code", 200) >= 400:
                logger.error("Supabase error fetching kingdom: %s", getattr(kingdom_res, "error", "unknown"))
                raise HTTPException(status_code=500, detail="Supabase query failed")

            kingdom_data = getattr(kingdom_res, "data", kingdom_res)
            if not kingdom_data or not kingdom_data.get("kingdom_id"):
                raise HTTPException(status_code=404, detail="Kingdom not found")

            kid = kingdom_data["kingdom_id"]

            # Fetch the kingdom's resource ledger
            res = (
                supabase.table("kingdom_resources")
                .select("*")
                .eq("kingdom_id", kid)
                .single()
                .execute()
            )
            if getattr(res, "status_code", 200) >= 400:
                logger.error("Supabase error fetching resources: %s", getattr(res, "error", "unknown"))
                raise HTTPException(status_code=500, detail="Supabase query failed")

            resource_row = getattr(res, "data", res)
            if not resource_row:
                raise HTTPException(status_code=404, detail="Resources not found")

            # Exclude metadata fields
            resources = {
                k: v for k, v in resource_row.items()
                if k not in {"kingdom_id", "created_at", "last_updated"}
            }

            return {"resources": resources}

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Error retrieving resources from Supabase")
            raise HTTPException(status_code=500, detail="Failed to fetch resources from Supabase") from exc

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
        if col.name not in {"kingdom_id", "created_at", "last_updated"}
    }

    return {"resources": resources}
