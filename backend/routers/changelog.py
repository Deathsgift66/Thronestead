from fastapi import APIRouter, Depends, HTTPException
from ..security import verify_jwt_token


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
    try:
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - library optional in tests
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)

router = APIRouter(prefix="/api/changelog", tags=["changelog"])


@router.get("")
async def get_changelog(user_id: str = Depends(verify_jwt_token)):
    """Return the public game changelog sorted by most recent."""
    supabase = get_supabase_client()

    res = (
        supabase
        .table("game_changelog")
        .select("*")
        .order("release_date", desc=True)
        .limit(50)
        .execute()
    )

    rows = getattr(res, "data", res) or []
    entries = [
        {
            "version": r.get("version"),
            "date": r.get("release_date"),
            "changes": r.get("changes") or [],
        }
        for r in rows
    ]

    return {"entries": entries}

