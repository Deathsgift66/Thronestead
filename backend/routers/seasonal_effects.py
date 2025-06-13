# Project Name: Kingmakers Rise©
# File Name: seasonal_effects.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException

from .navbar import get_supabase_client
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/seasonal-effects", tags=["seasonal_effects"])

@router.get("")
def seasonal_data(user_id: str = Depends(verify_jwt_token)):
    client = get_supabase_client()
    current_res = (
        client.table("seasonal_effects")
        .select("*")
        .eq("active", True)
        .single()
        .execute()
    )
    current = (
        current_res.get("data") if isinstance(current_res, dict) else getattr(current_res, "data", None)
    )
    if not current:
        raise HTTPException(status_code=404, detail="Current season not found")

    forecast_res = (
        client.table("seasonal_effects")
        .select("*")
        .order("start_date", ascending=True)
        .limit(4)
        .execute()
    )
    forecast = (
        forecast_res.get("data") if isinstance(forecast_res, dict) else getattr(forecast_res, "data", [])
    ) or []
    return {"current": current, "forecast": forecast}
