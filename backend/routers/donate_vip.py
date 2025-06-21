# Project Name: Thronestead©
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
