# Project Name: Thronestead©
# File Name: donate_vip.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: donate_vip.py
Role: API routes for donate vip.
Version: 2025-06-21
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.vip_status_service import get_vip_status, upsert_vip_status
from services.audit_service import log_action
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/vip", tags=["vip"])

# --------------------
# Pydantic Models
# --------------------
class DonationPayload(BaseModel):
    tier_id: int


# --------------------
# VIP Tier Definition
# --------------------
VIP_TIERS = {
    1: {
        "tier_name": "VIP 1",
        "price_gold": 300,
        "duration_days": 30,
        "perks": "Supporter badge and chat emote",
    },
    2: {
        "tier_name": "VIP 2",
        "price_gold": 500,
        "duration_days": 30,
        "perks": "All VIP1 perks plus banner",
    },
    3: {
        "tier_name": "VIP 3",
        "price_gold": 1000,
        "duration_days": 30,
        "perks": "All VIP2 perks plus skins",
    },
}


# --------------------
# Routes
# --------------------
@router.get("/status")
def vip_status(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return current VIP status for the logged-in user."""
    record = get_vip_status(db, user_id)
    return record or {"vip_level": 0, "expires_at": None, "founder": False}


@router.get("/tiers")
def vip_tiers(user_id: str = Depends(verify_jwt_token)):
    """Return available VIP tier options."""
    return {"tiers": [{"tier_id": tid, **data} for tid, data in VIP_TIERS.items()]}


@router.get("/leaderboard")
def vip_leaderboard(user_id: str = Depends(verify_jwt_token)):
    """Return top VIP donors from Supabase."""
    supabase = get_supabase_client()
    result = (
        supabase.table("vip_donations")
        .select("user_id, username, total_donated")
        .order("total_donated", desc=True)
        .limit(10)
        .execute()
    )
    leaders = getattr(result, "data", result) or []
    return {"leaders": leaders}


@router.post("/donate")
def donate(
    payload: DonationPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Donate for VIP tier (30-day duration unless founder)."""
    tier = VIP_TIERS.get(payload.tier_id)
    if not tier:
        raise HTTPException(status_code=400, detail="Invalid tier")

    record = get_vip_status(db, user_id) or {
        "vip_level": 0,
        "expires_at": None,
        "founder": False,
    }

    new_level = payload.tier_id
    is_founder = record.get("founder", False)

    # Founders get permanent max-tier status
    new_expires = None if is_founder else datetime.utcnow() + timedelta(days=tier["duration_days"])
    if is_founder:
        new_level = max(record["vip_level"], new_level)

    upsert_vip_status(db, user_id, new_level, new_expires, is_founder)
    log_action(db, user_id, "vip_donation", f"User upgraded to VIP {new_level}")
    return {"message": "ok"}
