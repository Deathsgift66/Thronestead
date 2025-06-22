# Project Name: Thronestead©
# File Name: black_market.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: black_market.py
Role: API routes for black market.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, conint, PositiveFloat
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import BlackMarketListing, TradeLog
from services.audit_service import log_action
from services.trade_log_service import record_trade
from services.vip_status_service import get_vip_status, is_vip_active
from services.resource_service import spend_resources, gain_resources
from ..security import require_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/black-market", tags=["black_market"])

ALLOWED_ITEM_TYPES = {"token", "cosmetic", "permit", "contraband", "artifact"}

# ---------------------
# Pydantic Schemas
# ---------------------
class ListingPayload(BaseModel):
    item: str
    item_type: str = "token"
    price: PositiveFloat
    quantity: conint(gt=0)


class BuyPayload(BaseModel):
    listing_id: int
    quantity: conint(gt=0)


class CancelPayload(BaseModel):
    listing_id: int

# ---------------------
# GET Market Listings
# ---------------------
@router.get("")
def get_market(
    item_type: str | None = Query(None),
    max_price: float | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return paginated black market listings."""
    query = db.query(BlackMarketListing)
    if item_type:
        query = query.filter(BlackMarketListing.item_type == item_type)
    if max_price is not None:
        query = query.filter(BlackMarketListing.price <= max_price)

    rows = (
        query.order_by(BlackMarketListing.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    listings = [
        {
            "listing_id": row.listing_id,
            "item": row.item,
            "price": float(row.price),
            "quantity": row.quantity,
            "seller": "Anonymous",
        }
        for row in rows
    ]
    return {"listings": listings}
