from fastapi import APIRouter, Depends, HTTPException
from ..security import verify_jwt_token
from pydantic import BaseModel


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
    try:
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - optional
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)


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
def cancel_listing(payload: ListingAction, user_id: str = Depends(verify_jwt_token)):
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
