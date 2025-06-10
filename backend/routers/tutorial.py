from fastapi import APIRouter, Depends, HTTPException

from .progression_router import get_user_id


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
    try:
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - library optional
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)


router = APIRouter(prefix="/api/tutorial", tags=["tutorial"])


@router.get("/steps")
async def steps(user_id: str = Depends(get_user_id)):
    """Return ordered tutorial steps from Supabase for the authenticated user."""
    supabase = get_supabase_client()

    user_check = (
        supabase.table("users").select("user_id").eq("user_id", user_id).single().execute()
    )
    if not getattr(user_check, "data", user_check):
        raise HTTPException(status_code=401, detail="Invalid user")

    res = (
        supabase.table("tutorial_steps")
        .select("id,title,description,step_number")
        .order("step_number")
        .execute()
    )
    rows = getattr(res, "data", res) or []
    steps = [
        {
            "step_id": r.get("id"),
            "title": r.get("title"),
            "description": r.get("description"),
            "step_number": r.get("step_number"),
        }
        for r in rows
    ]
    return {"steps": steps}
