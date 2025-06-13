# Project Name: Kingmakers Rise©
# File Name: market.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..security import verify_jwt_token
from ..database import get_db
from services.vacation_mode_service import check_vacation_mode
from .progression_router import get_kingdom_id
from pydantic import BaseModel


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/market", tags=["market"])


class ListingAction(BaseModel):
    listing_id: int


@router.get("/listings")
def listings(user_id: str = Depends(verify_jwt_token)):
    supabase = get_supabase_client()
    res = (
        supabase.table("market_listings")
        .select("listing_id,item_name,quantity,price,seller_name,seller_id")
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    rows = getattr(res, "data", res) or []
    return {"listings": rows}


@router.get("/my_listings")
def my_listings(user_id: str = Depends(verify_jwt_token)):
    supabase = get_supabase_client()
    res = (
        supabase.table("market_listings")
        .select("listing_id,item_name,quantity,price,seller_name")
        .eq("seller_id", user_id)
        .execute()
    )
    rows = getattr(res, "data", res) or []
    return {"listings": rows}


@router.post("/cancel_listing")
def cancel_listing(
    payload: ListingAction,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    check_vacation_mode(db, kid)
    supabase = get_supabase_client()
    listing_res = (
        supabase.table("market_listings")
        .select("seller_id")
        .eq("listing_id", payload.listing_id)
        .single()
        .execute()
    )
    listing = getattr(listing_res, "data", listing_res)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("seller_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot cancel another player's listing")
    supabase.table("market_listings").delete().eq("listing_id", payload.listing_id).execute()
    return {"message": "Listing cancelled"}


@router.get("/history")
def history(user_id: str = Depends(verify_jwt_token)):
    supabase = get_supabase_client()
    res = (
        supabase.table("trade_logs")
        .select("item_name,quantity,unit_price as price,buyer_name,seller_name,completed_at")
        .or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}")
        .order("completed_at", desc=True)
        .limit(50)
        .execute()
    )
    rows = getattr(res, "data", res) or []
    return {"trades": rows}
