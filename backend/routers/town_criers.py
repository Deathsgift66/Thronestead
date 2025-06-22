# Project Name: Thronestead©
# File Name: town_criers.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: town_criers.py
Role: API routes for town criers.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/town-criers", tags=["town criers"])


# ---------------------------
# Request Payload Models
# ---------------------------
class ScrollPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=5000)


# ---------------------------
# Routes
# ---------------------------

@router.get("/latest", summary="Fetch latest scrolls")
def latest_scrolls(user_id: str = Depends(verify_jwt_token)) -> dict:
    """
    Return recent town crier scrolls (latest 25) for authenticated users.
    """
    supabase = get_supabase_client()

    check = (
        supabase.table("users")
        .select("user_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if getattr(check, "error", None) or not getattr(check, "data", None):
        raise HTTPException(status_code=401, detail="Invalid user")

    try:
        res = (
            supabase.table("town_crier_scrolls")
            .select("id,title,body,author_display_name,created_at")
            .order("created_at", desc=True)
            .limit(25)
            .execute()
        )
        rows = getattr(res, "data", res) or []
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch scrolls") from e

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


@router.post("/post", summary="Post a new scroll")
def post_scroll(payload: ScrollPayload, user_id: str = Depends(verify_jwt_token)) -> dict:
    """
    Post a new town crier scroll authored by the current user.
    """
    supabase = get_supabase_client()
    prof = (
        supabase.table("users")
        .select("display_name")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    prof_row = getattr(prof, "data", prof)
    if getattr(prof, "error", None) or not prof_row:
        raise HTTPException(status_code=401, detail="Invalid user")

    record = {
        "author_id": user_id,
        "author_display_name": prof_row.get("display_name"),
        "title": payload.title,
        "body": payload.body,
    }

    try:
        res = supabase.table("town_crier_scrolls").insert(record).execute()
        if getattr(res, "status_code", 200) >= 400:
            raise HTTPException(status_code=500, detail="Failed to post scroll")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error posting scroll") from e

    return {"status": "posted"}
