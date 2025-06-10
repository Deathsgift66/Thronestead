from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/town-criers", tags=["town criers"])


class ScrollPayload(BaseModel):
    title: str
    body: str


@router.get("/latest")
async def latest_scrolls(user_id: str = Depends(verify_jwt_token)):
    """Return recent town crier scrolls for authenticated users."""
    supabase = get_supabase_client()

    check = (
        supabase.table("users").select("user_id").eq("user_id", user_id).single().execute()
    )
    if not getattr(check, "data", check):
        raise HTTPException(status_code=401, detail="Invalid user")

    res = (
        supabase.table("town_crier_scrolls")
        .select("id,title,body,author_display_name,created_at")
        .order("created_at", desc=True)
        .limit(25)
        .execute()
    )
    rows = getattr(res, "data", res) or []
    scrolls = [
        {
            "scroll_id": r.get("id"),
            "title": r.get("title"),
            "body": r.get("body"),
            "author_display_name": r.get("author_display_name"),
            "created_at": r.get("created_at"),
        }
        for r in rows
    ]
    return {"scrolls": scrolls}


@router.post("/post")
async def post_scroll(payload: ScrollPayload, user_id: str = Depends(verify_jwt_token)):
    supabase = get_supabase_client()
    prof = (
        supabase.table("users")
        .select("display_name")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    prof_row = getattr(prof, "data", prof)
    if not prof_row:
        raise HTTPException(status_code=401, detail="Invalid user")

    record = {
        "author_id": user_id,
        "author_display_name": prof_row.get("display_name"),
        "title": payload.title,
        "body": payload.body,
    }
    res = supabase.table("town_crier_scrolls").insert(record).execute()
    if getattr(res, "status_code", 200) >= 400:
        raise HTTPException(status_code=500, detail="Failed to post scroll")
    return {"status": "posted"}
