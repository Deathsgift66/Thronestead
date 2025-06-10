from fastapi import APIRouter, Depends
from ..security import verify_jwt_token


def get_supabase_client():
    try:
        from supabase import create_client
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)


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
