from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional


def get_supabase_client():
    """Return configured Supabase client or raise."""
    try:  # pragma: no cover - optional dependency
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - library missing
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)


router = APIRouter(prefix="/api/signup", tags=["signup"])


class CheckPayload(BaseModel):
    kingdom_name: Optional[str] = None
    username: Optional[str] = None


@router.post("/check")
async def check_availability(payload: CheckPayload):
    """Check if kingdom or username is available."""
    sb = get_supabase_client()
    available_kingdom = True
    available_username = True
    try:
        if payload.kingdom_name:
            res = (
                sb.table("kingdoms")
                .select("kingdom_id")
                .eq("kingdom_name", payload.kingdom_name)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", res) or []
            available_kingdom = len(rows) == 0
        if payload.username:
            res = (
                sb.table("users")
                .select("id")
                .eq("username", payload.username)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", res) or []
            available_username = len(rows) == 0
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="failed to query") from exc

    return {"kingdom_available": available_kingdom, "username_available": available_username}


@router.get("/stats")
async def signup_stats():
    """Return top kingdom stats for signup page."""
    sb = get_supabase_client()
    try:
        res = (
            sb.table("leaderboard_kingdoms")
            .select("kingdom_name,score")
            .order("score", desc=True)
            .limit(3)
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="failed to fetch stats") from exc

    data = getattr(res, "data", res) or []
    return {"top_kingdoms": data}
