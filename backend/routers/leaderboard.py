from fastapi import APIRouter, Depends, HTTPException

from ..security import verify_jwt_token


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
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

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/{type}")
async def leaderboard(type: str, user_id: str = Depends(verify_jwt_token)):
    """Return leaderboard data from Supabase."""
    table_map = {
        "kingdoms": "leaderboard_kingdoms",
        "alliances": "leaderboard_alliances",
        "wars": "leaderboard_wars",
        "economy": "leaderboard_economy",
    }
    table = table_map.get(type)
    if not table:
        raise HTTPException(status_code=400, detail="invalid leaderboard type")

    supabase = get_supabase_client()
    try:
        result = (
            supabase.table(table)
            .select("*")
            .limit(50)
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard") from exc

    entries = getattr(result, "data", result) or []
    return {"entries": entries}

