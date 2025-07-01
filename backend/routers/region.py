# Project Name: Thronestead©
# File Name: region.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""Region API endpoints for kingdom onboarding and setup."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/kingdom", tags=["kingdom"])


@router.get("/regions", response_class=JSONResponse)
def get_regions():
    """
    Fetch all available regions from the region_catalogue table.

    This is used during kingdom creation and setup to allow players
    to choose a region with strategic modifiers.
    """
    supabase = get_supabase_client()

    try:
        res = supabase.table("region_catalogue").select("*").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load regions") from e

    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail="Error fetching regions")

    regions = getattr(res, "data", res) or []
    return JSONResponse(content=regions)
