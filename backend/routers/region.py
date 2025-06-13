"""Region API endpoints for kingdom onboarding and setup."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/kingdom", tags=["kingdom"])


@router.get("/regions", response_class=JSONResponse)
def get_regions():
    """Return all regions from the region catalogue."""
    supabase = get_supabase_client()

    res = supabase.table("region_catalogue").select("*").execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail="Error fetching regions")

    regions = getattr(res, "data", res) or []

    return JSONResponse(content=regions)
