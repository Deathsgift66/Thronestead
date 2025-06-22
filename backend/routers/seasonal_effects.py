# Project Name: Thronestead©
# File Name: seasonal_effects.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from ..supabase_client import get_supabase_client
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/seasonal-effects", tags=["seasonal_effects"])


@router.get("", response_model=None)
def seasonal_data(user_id: str = Depends(verify_jwt_token)):
    """
    Return the current seasonal effect and a short forecast list.

    This endpoint is intended to support real-time gameplay changes and planning.
    """

    # Initialize Supabase client
    supabase = get_supabase_client()

    # Fetch the current active season (should only be one)
    try:
        current_res = (
            supabase.table("seasonal_effects")
            .select("*")
            .eq("active", True)
            .single()
            .execute()
        )
        current = (
            current_res.get("data") if isinstance(current_res, dict)
            else getattr(current_res, "data", None)
        )
        if not current:
            raise HTTPException(status_code=404, detail="Current season not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch current season") from e

    # Fetch the next 4 seasons by start date
    try:
        forecast_res = (
            supabase.table("seasonal_effects")
            .select("*")
            .order("start_date", ascending=True)
            .limit(4)
            .execute()
        )
        forecast = (
            forecast_res.get("data") if isinstance(forecast_res, dict)
            else getattr(forecast_res, "data", [])
        ) or []
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch seasonal forecast") from e

    return {"current": current, "forecast": forecast}
