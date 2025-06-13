# Project Name: Kingmakers Rise©
# File Name: treaty_web.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends
from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/treaty_web", tags=["treaty_web"])


@router.get("/data")
def treaty_web_data(user_id: str = Depends(verify_jwt_token)):
    """Return alliances, kingdoms and treaty records for the treaty web."""
    supabase = get_supabase_client()
    alliances = (
        supabase.table("alliances").select("alliance_id,name").execute()
    )
    kingdoms = (
        supabase.table("users").select("kingdom_id,kingdom_name").execute()
    )
    treaties = supabase.table("alliance_treaties").select("*").execute()
    return {
        "alliances": getattr(alliances, "data", alliances) or [],
        "kingdoms": getattr(kingdoms, "data", kingdoms) or [],
        "treaties": getattr(treaties, "data", treaties) or [],
    }
