from fastapi import APIRouter, HTTPException

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("/documents")
def list_documents():
    """Retrieve all legal documents (ToS, Privacy Policy, etc.)."""
    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("legal_documents")
            .select("id,title,summary,url,display_order")
            .order("display_order")
            .execute()
        )
        rows = getattr(response, "data", response) or []
    except Exception as e:  # pragma: no cover - network/DB issues
        raise HTTPException(status_code=500, detail="Failed to fetch documents") from e

    documents = [
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "summary": r.get("summary"),
            "url": r.get("url"),
        }
        for r in rows
    ]

    return {"documents": documents}
