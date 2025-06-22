# Project Name: Thronestead©
# File Name: system_changelog.py
# Version 6.14.2025
# Developer: OpenAI Codex

"""
Project: Thronestead ©
File: system_changelog.py
Role: API routes for system changelog.
Version: 2025-06-21
"""

from fastapi import APIRouter, HTTPException, Query
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/system/changelog", tags=["system_changelog"])


@router.get("", response_model=None)
def get_system_changelog(refresh: bool = Query(False, description="Force data refresh")):
    """Return the latest game changelog entries."""
    supabase = get_supabase_client()

    try:
        res = (
            supabase
            .table("game_changelog")
            .select("*")
            .order("release_date", desc=True)
            .limit(50)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve changelog: {str(e)}")

    rows = getattr(res, "data", res) or []
    entries = [
        {
            "version": r.get("version"),
            "title": r.get("title"),
            "date": r.get("release_date"),
            "changes": r.get("changes") or [],
        }
        for r in rows
        if r.get("version") and r.get("release_date")
    ]
    return entries
