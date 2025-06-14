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
    """
    Return the authenticated player's resource ledger.

    Supports Supabase for real-time cloud reads, with local SQL fallback.
    Filters out technical metadata like timestamps and IDs.
    """
    # ✅ Attempt Supabase first
    try:
        supabase = get_supabase_client()
    except RuntimeError:
        supabase = None  # 🔁 fallback enabled if Supabase is offline

    if supabase:
        try:
            # Step 1: Lookup kingdom ID via user_id
            kingdom_res = (
                supabase.table("kingdoms")
                .select("kingdom_id")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            kingdom_data = getattr(kingdom_res, "data", kingdom_res)
            if not kingdom_data or not kingdom_data.get("kingdom_id"):
                raise HTTPException(status_code=404, detail="Kingdom not found")

            kid = kingdom_data["kingdom_id"]

            # Step 2: Fetch kingdom resources
            res = (
                supabase.table("kingdom_resources")
                .select("*")
                .eq("kingdom_id", kid)
                .single()
                .execute()
            )
            row = getattr(res, "data", res)
            if not row:
                raise HTTPException(status_code=404, detail="Resources not found")

            # Step 3: Filter out metadata fields
            resources = {
                k: v
                for k, v in row.items()
                if k not in {"kingdom_id", "created_at", "last_updated"}
            }

            return {"resources": resources}

        except Exception as exc:
            raise HTTPException(status_code=500, detail="Supabase error") from exc

    # 🔁 Local SQLAlchemy fallback
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

    # Construct dict from ORM columns, excluding metadata
    resources = {
        col.name: getattr(row, col.name)
        for col in KingdomResources.__table__.columns
        if col.name not in {"kingdom_id", "created_at", "last_updated"}
    }

    return {"resources": resources}
