# Comment
# Project Name: Thronestead©
# File Name: changelog.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: changelog.py
Role: API routes for changelog.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException

from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/changelog", tags=["changelog"])


@router.get("")
def get_changelog(user_id: str = Depends(verify_jwt_token)):
    """
    Return the public game changelog sorted by most recent release.
    Requires user to be logged in for visibility.
    """
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("game_changelog")
            .select("*")
            .order("release_date", desc=True)
            .limit(50)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve changelog: {str(e)}"
        )

    rows = getattr(res, "data", res) or []

    entries = [
        {
            "version": r.get("version"),
            "date": r.get("release_date"),
            "changes": r.get("changes") or [],
        }
        for r in rows
        if r.get("version") and r.get("release_date")  # Ensures valid records only
    ]

    return {"entries": entries}
