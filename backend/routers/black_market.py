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
from pydantic import BaseModel, PositiveFloat, conint
from sqlalchemy.orm import Session

from backend.models import BlackMarketListing

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/black-market", tags=["black_market"])
alt_router = APIRouter(prefix="/api/black_market", tags=["black_market"])

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


# ---------------------
# Create Listing
# ---------------------
@router.post("/list")
@alt_router.post("/list")
def place_item(
    payload: ListingPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """List an item on the black market."""
    if payload.item_type not in ALLOWED_ITEM_TYPES:
        raise HTTPException(status_code=400, detail="Invalid item type")

    listing = BlackMarketListing(
        seller_id=user_id,
        item=payload.item,
        item_type=payload.item_type,
        price=payload.price,
        quantity=payload.quantity,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return {"listing_id": listing.listing_id}


# ---------------------
# Purchase Item
# ---------------------
@router.post("/purchase")
@alt_router.post("/purchase")
def buy_item(
    payload: BuyPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Purchase quantity from a black market listing."""
    listing = (
        db.query(BlackMarketListing)
        .filter_by(listing_id=payload.listing_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if payload.quantity > listing.quantity:
        raise HTTPException(status_code=400, detail="Not enough quantity available")

    if payload.quantity < listing.quantity:
        listing.quantity -= payload.quantity
    else:
        db.delete(listing)

    db.commit()
    return {"message": "Purchase complete", "listing_id": payload.listing_id}


# ---------------------
# Cancel Listing
# ---------------------
@router.post("/cancel")
@alt_router.post("/cancel")
def cancel_listing(
    payload: CancelPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Remove a listing created by the current user."""
    listing = (
        db.query(BlackMarketListing)
        .filter_by(listing_id=payload.listing_id, seller_id=user_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or unauthorized")
    db.delete(listing)
    db.commit()
    return {"message": "Listing cancelled"}
