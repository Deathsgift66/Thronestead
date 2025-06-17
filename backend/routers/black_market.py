# Project Name: Thronestead©
# File Name: black_market.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, conint, PositiveFloat
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import BlackMarketListing
from services.audit_service import log_action
from ..security import require_user_id

router = APIRouter(prefix="/api/black-market", tags=["black_market"])

# ---------------------
# Pydantic Schemas
# ---------------------
class ListingPayload(BaseModel):
    item: str
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
def get_market(db: Session = Depends(get_db)):
    """
    Return the 100 latest black market listings.
    """
    rows = (
        db.query(BlackMarketListing)
        .order_by(BlackMarketListing.created_at.desc())
        .limit(100)
        .all()
    )

    listings = [
        {
            "listing_id": row.listing_id,
            "item": row.item,
            "price": float(row.price),
            "quantity": row.quantity,
            "seller_id": str(row.seller_id) if row.seller_id else None,
        }
        for row in rows
    ]
    return {"listings": listings}

# ---------------------
# POST New Listing
# ---------------------
@router.post("/place")
def place_item(
    payload: ListingPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Place an item for sale in the black market.
    """
    listing = BlackMarketListing(
        seller_id=user_id,
        item=payload.item,
        price=payload.price,
        quantity=payload.quantity,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    log_action(db, user_id, "black_market_listing", f"{payload.quantity} {payload.item} for {payload.price}g ea")

    return {"message": "Listing created", "listing_id": listing.listing_id}

# ---------------------
# POST Buy Item
# ---------------------
@router.post("/buy")
def buy_item(
    payload: BuyPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Purchase a quantity of an item from the black market.
    """
    listing = db.query(BlackMarketListing).filter_by(listing_id=payload.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if payload.quantity > listing.quantity:
        raise HTTPException(status_code=400, detail="Not enough quantity available")

    # Adjust listing quantity or remove listing
    if payload.quantity < listing.quantity:
        listing.quantity -= payload.quantity
    else:
        db.delete(listing)

    db.commit()
    log_action(db, user_id, "black_market_purchase", f"Bought {payload.quantity} {listing.item} from listing {listing.listing_id}")
    return {"message": "Purchase complete", "listing_id": payload.listing_id}

# ---------------------
# POST Cancel Listing
# ---------------------
@router.post("/cancel")
def cancel_listing(
    payload: CancelPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Cancel your own black market listing.
    """
    listing = (
        db.query(BlackMarketListing)
        .filter_by(listing_id=payload.listing_id, seller_id=user_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or unauthorized")

    db.delete(listing)
    db.commit()

    log_action(db, user_id, "black_market_cancel", f"Cancelled listing {payload.listing_id}")
    return {"message": "Listing cancelled", "listing_id": payload.listing_id}
