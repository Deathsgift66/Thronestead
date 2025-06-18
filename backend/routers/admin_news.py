# Project Name: Thronestead©
# File Name: admin_news.py
# Version: 6.14.2025.21.01
# Developer: Codex
"""Admin endpoints for publishing news articles."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..security import require_user_id
from ..supabase_client import get_supabase_client
from .admin_dashboard import verify_admin
from ..database import get_db
from services.audit_service import log_action

router = APIRouter(prefix="/api/admin/news", tags=["admin_news"])


class NewsPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)


@router.post("/post", summary="Publish a news article")
def post_news(
    payload: NewsPayload,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Insert a new news article authored by an admin."""
    verify_admin(admin_user_id, db)
    supabase = get_supabase_client()

    prof = (
        supabase.table("users")
        .select("display_name")
        .eq("user_id", admin_user_id)
        .single()
        .execute()
    )
    prof_row = getattr(prof, "data", prof)
    if getattr(prof, "error", None) or not prof_row:
        raise HTTPException(status_code=401, detail="Invalid user")

    record = {
        "author_id": admin_user_id,
        "author_name": prof_row.get("display_name"),
        "title": payload.title,
        "summary": payload.summary,
        "content": payload.content,
    }

    try:
        res = supabase.table("news_articles").insert(record).execute()
        if getattr(res, "status_code", 200) >= 400:
            raise HTTPException(status_code=500, detail="Failed to publish article")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error publishing article") from e

    log_action(db, admin_user_id, "post_news", payload.title)
    return {"status": "posted"}

