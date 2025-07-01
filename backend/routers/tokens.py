# Project Name: Thronestead©
# File Name: tokens.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Endpoints for Black Market token balances and redemption."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.token_service import (
    TOKEN_EXPIRES,
    TOKEN_STEALABLE,
    add_tokens,
    consume_tokens,
    get_balance,
)
from services.vip_status_service import upsert_vip_status

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


class RedeemPayload(BaseModel):
    perk_id: str


class BuyPayload(BaseModel):
    package_id: int


PERK_CATALOG = {
    "vip1": {"cost": 1, "vip_level": 1},
    "vip2": {"cost": 2, "vip_level": 2},
}


TOKEN_PACKAGES = {
    1: 1,
    2: 3,
}


@router.get("/balance")
def token_balance(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    """Return current token balance and token properties."""
    tokens = get_balance(db, user_id)
    return {
        "tokens": tokens,
        "stealable": TOKEN_STEALABLE,
        "expires": TOKEN_EXPIRES,
    }


@router.post("/redeem")
def redeem_tokens(
    payload: RedeemPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Redeem tokens for a perk."""
    perk = PERK_CATALOG.get(payload.perk_id)
    if not perk:
        raise HTTPException(status_code=400, detail="Invalid perk")
    if not consume_tokens(db, user_id, perk["cost"]):
        raise HTTPException(status_code=400, detail="Insufficient tokens")
    expires = datetime.utcnow() + timedelta(days=30)
    upsert_vip_status(db, user_id, perk["vip_level"], expires)
    return {"message": "redeemed", "perk": payload.perk_id}


@router.post("/buy")
def buy_tokens(
    payload: BuyPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Add tokens to the user's balance for the selected package."""
    amount = TOKEN_PACKAGES.get(payload.package_id)
    if not amount:
        raise HTTPException(status_code=400, detail="Invalid package")
    add_tokens(db, user_id, amount)
    return {"message": "added", "tokens": amount}
