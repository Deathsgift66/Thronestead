# Project Name: Kingmakers Rise©
# File Name: resources.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import User, KingdomResources
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/resources", tags=["resources"])

@router.get("")
def get_resources(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return the player's kingdom resource ledger."""
    try:
        supabase = get_supabase_client()
    except RuntimeError:  # pragma: no cover - supabase not configured
        supabase = None

    if supabase is not None:
        # Fetch from Supabase if credentials are provided
        try:
            kingdom_res = (
                supabase.table("kingdoms")
                .select("kingdom_id")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
        except Exception as exc:  # pragma: no cover - network/db errors
            raise HTTPException(status_code=500, detail="Failed to fetch kingdom") from exc

        data = getattr(kingdom_res, "data", kingdom_res)
        if not data:
            raise HTTPException(status_code=404, detail="Kingdom not found")

        kid = data.get("kingdom_id")
        try:
            res = (
                supabase.table("kingdom_resources")
                .select("*")
                .eq("kingdom_id", kid)
                .single()
                .execute()
            )
        except Exception as exc:  # pragma: no cover - network/db errors
            raise HTTPException(status_code=500, detail="Failed to fetch resources") from exc

        row = getattr(res, "data", res)
        if not row:
            raise HTTPException(status_code=404, detail="Resources not found")

        resources = {
            k: row[k]
            for k in row.keys()
            if k not in ("kingdom_id", "created_at", "last_updated")
        }
        return {"resources": resources}

    # Default to SQLAlchemy database
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.kingdom_id:
        raise HTTPException(status_code=404, detail="Kingdom not found")

    row = db.query(KingdomResources).filter_by(kingdom_id=user.kingdom_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Resources not found")

    resources = {
        c.name: getattr(row, c.name) for c in KingdomResources.__table__.columns
    }
    return {"resources": resources}
