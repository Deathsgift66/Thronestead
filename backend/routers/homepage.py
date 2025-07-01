# Project Name: Thronestead©
# File Name: homepage.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: homepage.py
Role: API routes for homepage.
Version: 2025-06-21
"""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/homepage", tags=["homepage"])


class ArticleSummary(BaseModel):
    id: int | None = None
    title: str | None = None
    summary: str | None = None
    published_at: str | None = None


class FeaturedNewsResponse(BaseModel):
    articles: List[ArticleSummary]


@router.get(
    "/featured",
    summary="Homepage News",
    description="Fetches latest 5 published news articles for the homepage.",
)
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
        ArticleSummary(
            id=r.get("id"),
            title=r.get("title"),
            summary=r.get("summary"),
            published_at=r.get("published_at"),
        )
        for r in rows
    ]

    return FeaturedNewsResponse(articles=articles)
