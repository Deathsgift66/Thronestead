# Project Name: Kingmakers Rise©
# File Name: legal.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, HTTPException


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("/documents")
def list_documents():
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
