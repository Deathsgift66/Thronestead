# Comment
# Project Name: Thronestead©
# File Name: news.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: news.py
Role: API routes for news.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException

from ..security import require_user_id
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/articles")
async def articles(user_id: str = Depends(require_user_id)):
    """
    📰 Return the latest news articles visible to authenticated users.
    Validates user session via Supabase and retrieves news metadata.
    """
    supabase = get_supabase_client()

    # Validate user exists and is authorized
    user_check = (
        supabase.table("users")
        .select("user_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if getattr(user_check, "error", None) or not getattr(user_check, "data", None):
        raise HTTPException(status_code=401, detail="Invalid or unauthorized user")

    # Fetch latest articles (limit 20, most recent first)
    res = (
        supabase.table("news_articles")
        .select("id,title,summary,author_name,published_at")
        .order("published_at", desc=True)
        .limit(20)
        .execute()
    )

    # Parse results
    rows = getattr(res, "data", res) or []
    articles = [
        {
            "article_id": r.get("id"),
            "title": r.get("title"),
            "summary": r.get("summary"),
            "author_name": r.get("author_name"),
            "published_at": r.get("published_at"),
        }
        for r in rows
    ]
    return {"articles": articles}
