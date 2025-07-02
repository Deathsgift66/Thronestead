# Project Name: Thronestead©
# File Name: admin_news.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""Admin endpoints for publishing news articles."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id, verify_api_key
from ..supabase_client import get_supabase_client
from ..security import verify_admin

router = APIRouter(prefix="/api/admin/news", tags=["admin_news"])


class NewsPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)


@router.post("/post", summary="Publish a news article")
def post_news(
    payload: NewsPayload,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """
    Insert a new news article authored by an admin.
    """
    verify_admin(admin_user_id, db)
    supabase = get_supabase_client()

    # Fetch admin's display name for attribution
    try:
        prof = (
            supabase.table("users")
            .select("display_name")
            .eq("user_id", admin_user_id)
            .single()
            .execute()
        )
        prof_row = getattr(prof, "data", None) or getattr(prof, "json", {}).get("data")
        if not prof_row or getattr(prof, "error", None):
            raise HTTPException(status_code=401, detail="Invalid user")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to fetch author profile"
        ) from e

    # Prepare article record
    record = {
        "author_id": admin_user_id,
        "author_name": prof_row.get("display_name"),
        "title": payload.title,
        "summary": payload.summary,
        "content": payload.content,
    }

    # Insert article
    try:
        res = supabase.table("news_articles").insert(record).execute()
        if getattr(res, "status_code", 200) >= 400:
            raise HTTPException(status_code=500, detail="Failed to publish article")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error publishing article") from e

    # Audit log
    log_action(db, admin_user_id, "post_news", payload.title)
    return {"status": "posted"}
