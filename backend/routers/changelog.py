from fastapi import APIRouter, Depends
from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client

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

