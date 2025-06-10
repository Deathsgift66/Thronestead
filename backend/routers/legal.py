from fastapi import APIRouter, HTTPException


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


router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("/documents")
async def list_documents():
    """Return available legal documents sorted by display order."""
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("legal_documents")
            .select("id,title,summary,url,display_order")
            .order("display_order")
            .execute()
        )
    except Exception as e:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to fetch documents") from e

    rows = getattr(res, "data", res) or []
    docs = [
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "summary": r.get("summary"),
            "url": r.get("url"),
        }
        for r in rows
    ]
    return {"documents": docs}
