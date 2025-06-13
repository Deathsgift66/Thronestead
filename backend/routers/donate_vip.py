# Project Name: Kingmakers Rise©
# File Name: donate_vip.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.vip_status_service import get_vip_status, upsert_vip_status
from services.audit_service import log_action

router = APIRouter(prefix="/api/vip", tags=["vip"])


from ..supabase_client import get_supabase_client


class DonationPayload(BaseModel):
    tier_id: int


@router.get("/status")
def vip_status(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    record = get_vip_status(db, user_id)
    if not record:
        return {"vip_level": 0, "expires_at": None, "founder": False}
    return record


@router.get("/tiers")
def vip_tiers(user_id: str = Depends(verify_jwt_token)):
    return {
        "tiers": [
            {
                "tier_id": 1,
                "tier_name": "VIP 1",
                "price_gold": 300,
                "duration_days": 30,
                "perks": "Supporter badge and chat emote",
            },
            {
                "tier_id": 2,
                "tier_name": "VIP 2",
                "price_gold": 500,
                "duration_days": 30,
                "perks": "All VIP1 perks plus banner",
            },
            {
                "tier_id": 3,
                "tier_name": "VIP 3",
                "price_gold": 1000,
                "duration_days": 30,
                "perks": "All VIP2 perks plus skins",
            },
        ]
    }


@router.get("/leaders")
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
    # Demo implementation: upgrade VIP without charging
    tiers = {1: 300, 2: 500, 3: 1000}
    if payload.tier_id not in tiers:
        raise HTTPException(status_code=400, detail="invalid tier")

    record = get_vip_status(db, user_id) or {
        "vip_level": 0,
        "expires_at": None,
        "founder": False,
    }
    level = payload.tier_id
    expires_at = datetime.utcnow() + timedelta(days=30)
    if record.get("founder"):
        expires_at = None
        level = max(record.get("vip_level", 0), level)
    upsert_vip_status(db, user_id, level, expires_at, record.get("founder", False))
    log_action(db, user_id, "vip_donation", f"User upgraded to VIP {level}")
    return {"message": "ok"}
