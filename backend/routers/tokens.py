# Project Name: Thronestead©
# File Name: tokens.py
# Version: 6.14.2025
# Developer: Codex
"""Endpoints for Black Market token balances and redemption."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.token_service import get_balance, consume_tokens
from services.vip_status_service import upsert_vip_status

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


class RedeemPayload(BaseModel):
    perk_id: str


PERK_CATALOG = {
    "vip1": {"cost": 1, "vip_level": 1},
    "vip2": {"cost": 2, "vip_level": 2},
}


@router.get("/balance")
def token_balance(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return current token balance for the user."""
    tokens = get_balance(db, user_id)
    return {"tokens": tokens}


@router.post("/redeem")
def redeem_tokens(payload: RedeemPayload, user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Redeem tokens for a perk."""
    perk = PERK_CATALOG.get(payload.perk_id)
    if not perk:
        raise HTTPException(status_code=400, detail="Invalid perk")
    if not consume_tokens(db, user_id, perk["cost"]):
        raise HTTPException(status_code=400, detail="Insufficient tokens")
    expires = datetime.utcnow() + timedelta(days=30)
    upsert_vip_status(db, user_id, perk["vip_level"], expires)
    return {"message": "redeemed", "perk": payload.perk_id}
