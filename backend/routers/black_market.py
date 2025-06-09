from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BlackMarketListing, User
from services.trade_log_service import record_trade

router = APIRouter(prefix="/api/black-market", tags=["black_market"])


class ListingPayload(BaseModel):
    seller_id: str
    item: str
    price: float
    quantity: int


class BuyPayload(BaseModel):
    listing_id: int
    quantity: int
    buyer_id: str


class CancelPayload(BaseModel):
    listing_id: int
    seller_id: str


@router.get("")
def get_market(db: Session = Depends(get_db)):
    rows = (
        db.query(BlackMarketListing, User.username.label("seller"))
        .join(User, User.user_id == BlackMarketListing.seller_id)
        .order_by(BlackMarketListing.created_at.desc())
        .limit(100)
        .all()
    )
    listings = [
        {
            "id": r.BlackMarketListing.listing_id,
            "item": r.BlackMarketListing.item,
            "price": float(r.BlackMarketListing.price),
            "quantity": r.BlackMarketListing.quantity,
            "seller": r.seller,
        }
        for r in rows
    ]
    return {"listings": listings}


@router.post("/place")
def place_item(payload: ListingPayload, db: Session = Depends(get_db)):
    listing = BlackMarketListing(
        seller_id=payload.seller_id,
        item=payload.item,
        price=payload.price,
        quantity=payload.quantity,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return {"message": "Listing created", "listing_id": listing.listing_id}


@router.post("/buy")
def buy_item(payload: BuyPayload, db: Session = Depends(get_db)):
    listing = (
        db.query(BlackMarketListing)
        .filter(BlackMarketListing.listing_id == payload.listing_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if payload.quantity > listing.quantity:
        raise HTTPException(status_code=400, detail="Not enough quantity")

    if payload.quantity < listing.quantity:
        listing.quantity -= payload.quantity
        db.commit()
    else:
        db.delete(listing)
        db.commit()

    record_trade(
        db,
        resource=listing.item,
        quantity=payload.quantity,
        unit_price=float(listing.price),
        buyer_id=payload.buyer_id,
        seller_id=str(listing.seller_id),
        buyer_alliance_id=None,
        seller_alliance_id=None,
        buyer_name=None,
        seller_name=None,
        trade_type="black_market",
    )

    return {"message": "Purchase complete", "listing_id": payload.listing_id}


@router.post("/cancel")
def cancel_listing(payload: CancelPayload, db: Session = Depends(get_db)):
    listing = (
        db.query(BlackMarketListing)
        .filter(
            BlackMarketListing.listing_id == payload.listing_id,
            BlackMarketListing.seller_id == payload.seller_id,
        )
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    db.delete(listing)
    db.commit()
    return {"message": "Listing cancelled", "listing_id": payload.listing_id}
