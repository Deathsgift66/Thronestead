# Project Name: Thronestead©
# File Name: system_changelog.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: system_changelog.py
Role: API routes for system changelog.
Version: 2025-06-21
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict

from fastapi import APIRouter, HTTPException, Query

from ..supabase_client import get_supabase_client
from ..data import system_changelog_entries

router = APIRouter(prefix="/api/system/changelog", tags=["system_changelog"])

logger = logging.getLogger(__name__)

_CACHE_TTL = timedelta(hours=1)
_last_loaded: datetime | None = None


def _fetch_changelog(limit: int = 50) -> List[Dict]:
    """Retrieve changelog entries from Supabase."""
    supabase = get_supabase_client()
    res = (
        supabase.table("game_changelog")
        .select("*")
        .order("release_date", desc=True)
        .limit(limit)
        .execute()
    )
    rows = getattr(res, "data", res) or []
    return [
        {
            "version": r.get("version"),
            "title": r.get("title"),
            "date": r.get("release_date"),
            "changes": r.get("changes") or [],
        }
        for r in rows
        if r.get("version") and r.get("release_date")
    ]


@router.get("")
def get_system_changelog(
    refresh: bool = Query(False, description="Force data refresh")
) -> List[Dict]:
    """Return cached changelog entries with optional refresh."""
    global _last_loaded

    now = datetime.utcnow()
    data_expired = (
        _last_loaded is None or now - _last_loaded > _CACHE_TTL
    )

    if refresh or data_expired or not system_changelog_entries:
        try:
            entries = _fetch_changelog()
        except Exception as e:  # pragma: no cover - network failure
            logger.exception("Failed to retrieve changelog")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve changelog: {e}",
            ) from e

        system_changelog_entries.clear()
        system_changelog_entries.extend(entries)
        _last_loaded = now

    return system_changelog_entries
