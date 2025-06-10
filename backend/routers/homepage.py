from fastapi import APIRouter, HTTPException


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/homepage", tags=["homepage"])


@router.get("/featured")
async def featured_news():
    """Return latest news articles for the homepage."""
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("news_articles")
            .select("id,title,summary,published_at")
            .order("published_at", desc=True)
            .limit(5)
            .execute()
        )
    except Exception as e:  # pragma: no cover - network/db errors
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

