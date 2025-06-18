from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, conint, PositiveFloat
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from ..models import MarketListing
from services.trade_log_service import record_trade

router = APIRouter(prefix="/api/market", tags=["market"])


class ListingPayload(BaseModel):
    item_type: str
    item: str
    price: PositiveFloat
    quantity: conint(gt=0) = 1


class BuyPayload(BaseModel):
    listing_id: int
    quantity: conint(gt=0)


@router.get("/listings")
def get_listings(db: Session = Depends(get_db)):
    rows = (
        db.query(MarketListing)
        .order_by(MarketListing.created_at.desc())
        .all()
    )
    listings = [
        {
            "listing_id": r.listing_id,
            "item": r.item,
            "item_type": r.item_type,
            "price": float(r.price),
            "quantity": r.quantity,
            "seller_id": str(r.seller_id) if r.seller_id else None,
        }
        for r in rows
    ]
    return {"listings": listings}


@router.post("/list")
def list_item(
    payload: ListingPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    if payload.item_type not in {"resource", "equipment"}:
        raise HTTPException(status_code=400, detail="Invalid item type")

    listing = MarketListing(
        seller_id=user_id,
        item_type=payload.item_type,
        item=payload.item,
        price=payload.price,
        quantity=payload.quantity,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    return {"listing_id": listing.listing_id}


@router.delete("/listing/{listing_id}")
def cancel_listing(
    listing_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    listing = (
        db.query(MarketListing)
        .filter_by(listing_id=listing_id, seller_id=user_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or unauthorized")

    db.delete(listing)
    db.commit()
    return {"message": "Listing cancelled"}


@router.post("/buy")
def buy_item(
    payload: BuyPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    listing = db.query(MarketListing).filter_by(listing_id=payload.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if payload.quantity > listing.quantity:
        raise HTTPException(status_code=400, detail="Not enough quantity available")

    if payload.quantity < listing.quantity:
        listing.quantity -= payload.quantity
    else:
        db.delete(listing)

    db.commit()

    record_trade(
        db,
        resource=listing.item,
        quantity=payload.quantity,
        unit_price=float(listing.price),
        buyer_id=user_id,
        seller_id=str(listing.seller_id) if listing.seller_id else None,
        buyer_alliance_id=None,
        seller_alliance_id=None,
        buyer_name=None,
        seller_name=None,
        trade_type="market_sale",
    )

    return {"message": "Purchase complete", "listing_id": payload.listing_id}
