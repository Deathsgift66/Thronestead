# Project Name: Thronestead©
# File Name: black_market.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

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

# ---------------------
# POST New Listing
# ---------------------
@router.post("/place")
def place_item(
    payload: ListingPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Place an item for sale in the black market."""
    if payload.item_type not in ALLOWED_ITEM_TYPES:
        raise HTTPException(status_code=400, detail="Invalid item type")

    vip = get_vip_status(db, user_id)
    if not is_vip_active(vip):
        raise HTTPException(status_code=403, detail="VIP level required")

    try:
        kid = get_kingdom_id(db, user_id)
        spend_resources(db, kid, {payload.item: payload.quantity})
    except Exception:
        pass

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

    log_action(db, user_id, "black_market_listing", f"{payload.quantity} {payload.item} for {payload.price}g ea")
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
        trade_type="black_market",
        trade_status="listed",
    )

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

    buyer_kid = None
    seller_kid = None
    total_cost = listing.price * payload.quantity
    try:
        buyer_kid = get_kingdom_id(db, user_id)
        spend_resources(db, buyer_kid, {"gold": int(total_cost)})
    except Exception:
        pass
    try:
        seller_kid = get_kingdom_id(db, str(listing.seller_id)) if listing.seller_id else None
        if seller_kid:
            gain_resources(db, seller_kid, {"gold": int(total_cost)})
    except Exception:
        pass
    try:
        if buyer_kid:
            gain_resources(db, buyer_kid, {listing.item: payload.quantity})
    except Exception:
        pass

    # Adjust listing quantity or remove listing
    if payload.quantity < listing.quantity:
        listing.quantity -= payload.quantity
    else:
        db.delete(listing)

    db.commit()
    log_action(db, user_id, "black_market_purchase", f"Bought {payload.quantity} {listing.item} from listing {listing.listing_id}")
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
        trade_type="black_market",
    )
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
    try:
        kid = get_kingdom_id(db, user_id)
        gain_resources(db, kid, {listing.item: listing.quantity})
    except Exception:
        pass

    db.delete(listing)
    db.commit()

    log_action(db, user_id, "black_market_cancel", f"Cancelled listing {payload.listing_id}")
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
        trade_type="black_market",
        trade_status="cancelled",
    )
    return {"message": "Listing cancelled", "listing_id": payload.listing_id}


@router.get("/history/{player_id}")
def get_black_market_history(player_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(TradeLog)
        .filter(
            TradeLog.trade_type == "black_market",
            or_(TradeLog.buyer_id == player_id, TradeLog.seller_id == player_id),
        )
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
            "trade_status": r.trade_status,
        }
        for r in rows
    ]
    return {"logs": logs}
