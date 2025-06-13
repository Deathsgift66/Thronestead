from fastapi import APIRouter, Depends, HTTPException

from ..security import require_user_id


from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/articles")

async def articles(user_id: str = Depends(require_user_id)):

    """Return the latest news articles visible to authenticated users."""
    supabase = get_supabase_client()

    user_check = (
        supabase.table("users").select("user_id").eq("user_id", user_id).single().execute()
    )
    if getattr(user_check, "error", None) or not getattr(user_check, "data", None):
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

