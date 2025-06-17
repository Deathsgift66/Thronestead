# Project Name: Thronestead©
# File Name: black_market_routes.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, conint
from typing import List
from datetime import datetime, timedelta

from ..security import verify_jwt_token

router = APIRouter(prefix="/api/black-market", tags=["black_market_v2"])

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
]

_transactions: List[Transaction] = []

_resources: dict[str, dict[str, int]] = {
    "demo-kingdom": {"gold": 100, "gems": 20}
}

# ---------------------------------------------
# Routes
# ---------------------------------------------

@router.get("/listings")
def get_listings() -> dict:
    """
    Return all active, non-expired black market listings.
    """
    now = datetime.utcnow()
    active_listings = [
        listing
        for listing in _listings
        if listing.stock_remaining > 0 and listing.expires_at > now
    ]
    return {"listings": [listing.dict() for listing in active_listings]}


@router.post("/purchase")
def purchase_item(
    payload: PurchasePayload,
    user_id: str = Depends(verify_jwt_token),
):
    """
    Purchase an item from the black market.
    Validates inventory, kingdom match, and funds.
    """
    if user_id != payload.kingdom_id:
        raise HTTPException(status_code=403, detail="Kingdom mismatch")

    listing = next(
        (item for item in _listings if item.id == payload.listing_id),
        None,
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Listing expired")
    if listing.stock_remaining < payload.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    kingdom_resources = _resources.setdefault(payload.kingdom_id, {"gold": 0, "gems": 0})
    total_cost = listing.price_per_unit * payload.quantity

    if kingdom_resources.get(listing.currency_type, 0) < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Apply transaction
    kingdom_resources[listing.currency_type] -= total_cost
    listing.stock_remaining -= payload.quantity

    # Record the transaction
    _transactions.append(Transaction(
        kingdom_id=payload.kingdom_id,
        black_market_offer_id=listing.id,
        item_name=listing.item_name,
        quantity=payload.quantity,
        price_per_unit=listing.price_per_unit,
        currency_type=listing.currency_type,
        purchased_at=datetime.utcnow()
    ))

    return {
        "message": "Purchase successful",
        "listing_id": listing.id,
        "stock_remaining": listing.stock_remaining,
        "kingdom_resources": kingdom_resources
    }

# Backwards compatibility aliases
purchase = purchase_item


@router.get("/history")
def get_history(
    kingdom_id: str,
    user_id: str = Depends(verify_jwt_token)
):
    """
    View last 10 transactions for your kingdom.
    """
    if user_id != kingdom_id:
        raise HTTPException(status_code=403, detail="Kingdom mismatch")

    history = [t.dict() for t in _transactions if t.kingdom_id == kingdom_id]
    return {"trades": history[-10:]}

# Backwards compatibility alias
history = get_history
