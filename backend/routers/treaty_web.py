# Project Name: Thronestead©
# File Name: treaty_web.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/treaty_web", tags=["treaty_web"])


@router.get("/data", summary="Load Treaty Web Data")
def treaty_web_data(user_id: str = Depends(verify_jwt_token)):
    """
    Return all active data required for rendering the full treaty web:
    - Alliance basic info
    - Kingdom basic info
    - All current alliance treaties
    """
    supabase = get_supabase_client()

    try:
        alliances_res = supabase.table("alliances").select("alliance_id,name").execute()
        kingdoms_res = supabase.table("users").select("kingdom_id,kingdom_name").execute()
        treaties_res = supabase.table("alliance_treaties").select("*").execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to load treaty web data") from exc

    return {
        "alliances": getattr(alliances_res, "data", alliances_res) or [],
        "kingdoms": getattr(kingdoms_res, "data", kingdoms_res) or [],
        "treaties": getattr(treaties_res, "data", treaties_res) or [],
    }
