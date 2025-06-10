from fastapi import APIRouter, Depends, HTTPException

from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client

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

