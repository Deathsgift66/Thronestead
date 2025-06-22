# Project Name: Thronestead©
# File Name: black_market_routes.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: black_market_routes.py
Role: API routes for black market routes.
Version: 2025-06-21
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, conint
from typing import List
from datetime import datetime, timedelta

from ..security import verify_jwt_token

router = APIRouter(prefix="/api/black-market", tags=["black_market_v2"])
alt_router = APIRouter(prefix="/api/black_market", tags=["black_market_v2"])

# ---------------------------------------------
# Pydantic Models
# ---------------------------------------------

class Listing(BaseModel):
    id: int
    item_key: str
    item_name: str
    description: str
    quantity: conint(gt=0)
    price_per_unit: int
    currency_type: str
    stock_remaining: conint(ge=0)
    expires_at: datetime

class PurchasePayload(BaseModel):
    listing_id: int
    quantity: conint(gt=0)
    kingdom_id: str

class Transaction(BaseModel):
    kingdom_id: str
    black_market_offer_id: int
    item_name: str
    quantity: int
    price_per_unit: int
    currency_type: str
    purchased_at: datetime

# ---------------------------------------------
# In-memory Store (stubbed for testing/demo)
# ---------------------------------------------
_listings: List[Listing] = [
    Listing(
        id=1,
        item_key="iron_sword",
        item_name="Iron Sword",
        description="A sturdy iron sword forged for battle.",
        quantity=50,
        price_per_unit=10,
        currency_type="gold",
        stock_remaining=50,
        expires_at=datetime.utcnow() + timedelta(days=1)
    ),
    Listing(
        id=2,
        item_key="royal_gem",
        item_name="Royal Gem",
        description="A rare and precious gem with magical properties.",
        quantity=5,
        price_per_unit=30,
        currency_type="gems",
        stock_remaining=5,
        expires_at=datetime.utcnow() + timedelta(hours=12)
    ),
    Listing(
        id=3,
        item_key="vip_token",
        item_name="VIP Token",
        description="Token used to unlock VIP features.",
        quantity=10,
        price_per_unit=15,
        currency_type="gems",
        stock_remaining=10,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    ),
]

_transactions: List[Transaction] = []

_resources: dict[str, dict[str, int]] = {
    "demo-kingdom": {"gold": 100, "gems": 20}
}

# ---------------------------------------------
# Routes
# ---------------------------------------------


@router.get("/listings", response_model=None)
@alt_router.get("/listings")
def get_listings():
    """Return available black market offers."""
    return {"listings": [l.model_dump() for l in _listings]}


@router.post("/purchase", response_model=None)
@alt_router.post("/purchase")
def purchase(payload: PurchasePayload, user_id: str = Depends(verify_jwt_token)):
    """Purchase an item from the in-memory market."""
    for listing in list(_listings):
        if listing.id == payload.listing_id:
            if payload.quantity > listing.stock_remaining:
                raise HTTPException(status_code=400, detail="Not enough stock")

            listing.stock_remaining -= payload.quantity
            _resources.setdefault(payload.kingdom_id, {"gold": 0, "gems": 0})
            cost = payload.quantity * listing.price_per_unit
            _resources[payload.kingdom_id][listing.currency_type] -= cost

            _transactions.append(
                Transaction(
                    kingdom_id=payload.kingdom_id,
                    black_market_offer_id=listing.id,
                    item_name=listing.item_name,
                    quantity=payload.quantity,
                    price_per_unit=listing.price_per_unit,
                    currency_type=listing.currency_type,
                    purchased_at=datetime.utcnow(),
                )
            )

            if listing.stock_remaining <= 0:
                _listings.remove(listing)

            return {"message": "Purchase complete"}

    raise HTTPException(status_code=404, detail="Listing not found")


@router.get("/history", response_model=None)
@alt_router.get("/history")
def history(kingdom_id: str):
    """Return purchase history for a kingdom."""
    trades = [t.model_dump() for t in _transactions if t.kingdom_id == kingdom_id]
    return {"trades": trades}

