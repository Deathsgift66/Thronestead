from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, conint, PositiveFloat
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from ..models import MarketListing, TradeLog
from services.trade_log_service import record_trade
from services.resource_service import spend_resources, gain_resources
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/market", tags=["market"])


class ListingPayload(BaseModel):
    item_type: str
    item: str
    price: PositiveFloat
    quantity: conint(gt=0) = 1


class BuyPayload(BaseModel):
    listing_id: int
    quantity: conint(gt=0)


@router.get("/listings", response_model=None)
def get_listings(
    item: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    alliance_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(MarketListing)
    if item:
        query = query.filter(MarketListing.item == item)
    if min_price is not None:
        query = query.filter(MarketListing.price >= min_price)
    if max_price is not None:
        query = query.filter(MarketListing.price <= max_price)
    if alliance_id is not None:
        query = query.filter(MarketListing.seller_id.in_(
            db.query(TradeLog.seller_id).filter(TradeLog.seller_alliance_id == alliance_id)
        ))

    rows = (
        query.order_by(MarketListing.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
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


@router.post("/list", response_model=None)
def list_item(
    payload: ListingPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    if payload.item_type not in {"resource", "equipment"}:
        raise HTTPException(status_code=400, detail="Invalid item type")
    # optional resource validation
    try:
        kid = get_kingdom_id(db, user_id)
        spend_resources(db, kid, {payload.item: payload.quantity})
    except Exception:
        pass

    existing = (
        db.query(MarketListing)
        .filter_by(
            seller_id=user_id,
            item=payload.item,
            item_type=payload.item_type,
            price=payload.price,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Duplicate listing")

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

    record_trade(
        db,
        resource=payload.item,
        quantity=payload.quantity,
        unit_price=float(payload.price),
        buyer_id=None,
        seller_id=user_id,
        buyer_alliance_id=None,
        seller_alliance_id=None,
        buyer_name=None,
        seller_name=None,
        trade_type="market_sale",
        trade_status="listed",
    )

    return {"listing_id": listing.listing_id}


@router.delete("/listing/{listing_id}", response_model=None)
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
    try:
        kid = get_kingdom_id(db, user_id)
        gain_resources(db, kid, {listing.item: listing.quantity})
    except Exception:
        pass

    db.delete(listing)
    db.commit()
    record_trade(
        db,
        resource=listing.item,
        quantity=listing.quantity,
        unit_price=float(listing.price),
        buyer_id=None,
        seller_id=user_id,
        buyer_alliance_id=None,
        seller_alliance_id=None,
        buyer_name=None,
        seller_name=None,
        trade_type="market_sale",
        trade_status="cancelled",
    )
    return {"message": "Listing cancelled"}


@router.post("/buy", response_model=None)
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

    buyer_kid = None
    seller_kid = None
    try:
        buyer_kid = get_kingdom_id(db, user_id)
        spend_resources(db, buyer_kid, {"gold": int(listing.price * payload.quantity)})
    except Exception:
        pass
    try:
        seller_kid = get_kingdom_id(db, str(listing.seller_id)) if listing.seller_id else None
        if seller_kid:
            gain_resources(db, seller_kid, {"gold": int(listing.price * payload.quantity)})
    except Exception:
        pass

    try:
        if buyer_kid:
            gain_resources(db, buyer_kid, {listing.item: payload.quantity})
    except Exception:
        pass

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


@router.get("/history/{player_id}", response_model=None)
def get_trade_history(player_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(TradeLog)
        .filter(or_(TradeLog.buyer_id == player_id, TradeLog.seller_id == player_id))
        .order_by(TradeLog.timestamp.desc())
        .limit(100)
        .all()
    )
    logs = [
        {
            "trade_id": r.trade_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "resource": r.resource,
            "quantity": r.quantity,
            "unit_price": float(r.unit_price) if r.unit_price is not None else None,
            "buyer_id": str(r.buyer_id) if r.buyer_id else None,
            "seller_id": str(r.seller_id) if r.seller_id else None,
            "trade_type": r.trade_type,
            "trade_status": r.trade_status,
        }
        for r in rows
    ]
    return {"logs": logs}
