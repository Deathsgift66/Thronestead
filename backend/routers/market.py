# Project Name: Kingmakers Rise©
# File Name: market.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from .progression_router import get_kingdom_id
from services.vacation_mode_service import check_vacation_mode
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/market", tags=["market"])


class ListingAction(BaseModel):
    listing_id: int


@router.get("/listings")
def listings(user_id: str = Depends(verify_jwt_token)):
    """
    📦 Public market listings, newest first.
    """
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("market_listings")
            .select("listing_id,item_name,quantity,price,seller_name,seller_id")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        listings = getattr(res, "data", res) or []
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load listings") from e

    return {"listings": listings}


@router.get("/my_listings")
def my_listings(user_id: str = Depends(verify_jwt_token)):
    """
    📋 Fetch market listings created by the current user.
    """
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("market_listings")
            .select("listing_id,item_name,quantity,price,seller_name")
            .eq("seller_id", user_id)
            .execute()
        )
        listings = getattr(res, "data", res) or []
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not fetch your listings") from e

    return {"listings": listings}


@router.post("/cancel_listing")
def cancel_listing(
    payload: ListingAction,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    ❌ Cancel an active market listing.
    Requires the user to be the seller and not in vacation mode.
    """
    kid = get_kingdom_id(db, user_id)
    check_vacation_mode(db, kid)

    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("market_listings")
            .select("seller_id")
            .eq("listing_id", payload.listing_id)
            .single()
            .execute()
        )
        listing = getattr(result, "data", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch listing") from e

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("seller_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot cancel another player's listing")

    try:
        supabase.table("market_listings").delete().eq("listing_id", payload.listing_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cancel listing") from e

    return {"message": "Listing cancelled"}


@router.get("/history")
def history(user_id: str = Depends(verify_jwt_token)):
    """
    🧾 Get the most recent trades involving the user.
    """
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("trade_logs")
            .select("item_name,quantity,unit_price as price,buyer_name,seller_name,completed_at")
            .or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}")
            .order("completed_at", desc=True)
            .limit(50)
            .execute()
        )
        trades = getattr(res, "data", res) or []
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch trade history") from e

    return {"trades": trades}
