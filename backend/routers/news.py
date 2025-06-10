from fastapi import APIRouter, Depends, HTTPException

from .progression_router import get_user_id


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
    try:
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - optional
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/articles")
async def articles(user_id: str = Depends(get_user_id)):
    """Return the latest news articles visible to authenticated users."""
    supabase = get_supabase_client()

    user_check = (
        supabase.table("users").select("user_id").eq("user_id", user_id).single().execute()
    )
    if not getattr(user_check, "data", user_check):
        raise HTTPException(status_code=401, detail="Invalid user")

    res = (
        supabase.table("news_articles")
        .select("id,title,summary,author_name,published_at")
        .order("published_at", desc=True)
        .limit(20)
        .execute()
    )
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

