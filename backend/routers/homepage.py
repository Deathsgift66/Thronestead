# Project Name: Thronestead©
# File Name: homepage.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: homepage.py
Role: API routes for homepage.
Version: 2025-06-21
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/homepage", tags=["homepage"])


@router.get("/featured", response_model=Dict[str, List[Dict]], summary="Homepage News", description="Fetches latest 5 published news articles for the homepage.")
def featured_news():
    """
    ✅ Pulls the 5 most recent news articles from the `news_articles` table in Supabase.
    Fields included: `id`, `title`, `summary`, `published_at`
    """
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("news_articles")
            .select("id,title,summary,published_at")
            .order("published_at", desc=True)
            .limit(5)
            .execute()
        )
    except Exception as e:  # Catches Supabase fetch or connectivity failures
        raise HTTPException(status_code=500, detail="Failed to fetch news") from e

    rows = getattr(res, "data", res) or []
    articles = [
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "summary": r.get("summary"),
            "published_at": r.get("published_at"),
        }
        for r in rows
    ]

    return {"articles": articles}
