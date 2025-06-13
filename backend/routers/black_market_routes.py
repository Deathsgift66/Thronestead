# Project Name: Kingmakers Rise©
# File Name: black_market_routes.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, HTTPException, Depends
from fastapi.params import Depends as DependsClass
from ..security import verify_jwt_token
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/black-market", tags=["black_market_v2"])

# --- In-memory store for demo purposes ---
class Listing(BaseModel):
    id: int
    item_key: str
    item_name: str
    description: str
    quantity: int
    price_per_unit: int
    currency_type: str
    stock_remaining: int
    expires_at: datetime

class PurchasePayload(BaseModel):
    listing_id: int
    quantity: int
    kingdom_id: str

class Transaction(BaseModel):
    kingdom_id: str
    black_market_offer_id: int
    item_name: str
    quantity: int
    price_per_unit: int
    currency_type: str
    purchased_at: datetime

# sample starting data
_listings: List[Listing] = [
    Listing(id=1, item_key="iron_sword", item_name="Iron Sword", description="A sturdy sword.",
            quantity=50, price_per_unit=10, currency_type="gold", stock_remaining=50,
            expires_at=datetime.utcnow() + timedelta(days=1)),
    Listing(id=2, item_key="royal_gem", item_name="Royal Gem", description="Shiny gem.",
            quantity=5, price_per_unit=30, currency_type="gems", stock_remaining=5,
            expires_at=datetime.utcnow() + timedelta(hours=12)),
]
_transactions: List[Transaction] = []
_resources = {
    "demo-kingdom": {"gold": 100, "gems": 20}
}

# --- Routes ---
@router.get("/listings")
def get_listings() -> dict:
    active = [l for l in _listings if l.stock_remaining > 0 and l.expires_at > datetime.utcnow()]
    return {"listings": [l.dict() for l in active]}


@router.post("/purchase")
def purchase(payload: PurchasePayload, user_id: str | None = Depends(verify_jwt_token)):
    if isinstance(user_id, DependsClass):
        user_id = payload.kingdom_id
    if user_id != payload.kingdom_id:
        raise HTTPException(status_code=403, detail="Kingdom mismatch")
    listing = next((l for l in _listings if l.id == payload.listing_id), None)
    if not listing or listing.stock_remaining < payload.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    kingdom = _resources.setdefault(payload.kingdom_id, {"gold": 0, "gems": 0})
    cost = listing.price_per_unit * payload.quantity
    if kingdom.get(listing.currency_type, 0) < cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    kingdom[listing.currency_type] -= cost
    listing.stock_remaining -= payload.quantity

    _transactions.append(Transaction(
        kingdom_id=payload.kingdom_id,
        black_market_offer_id=listing.id,
        item_name=listing.item_name,
        quantity=payload.quantity,
        price_per_unit=listing.price_per_unit,
        currency_type=listing.currency_type,
        purchased_at=datetime.utcnow()
    ))
    return {"success": True, "remaining": listing.stock_remaining}


@router.get("/history")
def history(kingdom_id: str, user_id: str | None = Depends(verify_jwt_token)):
    if isinstance(user_id, DependsClass):
        user_id = kingdom_id
    if user_id != kingdom_id:
        raise HTTPException(status_code=403, detail="Kingdom mismatch")
    history = [t.dict() for t in _transactions if t.kingdom_id == kingdom_id]
    return {"trades": history[-10:]}
