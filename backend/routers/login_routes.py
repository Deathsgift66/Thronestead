from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.audit_service import log_action


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/login", tags=["login"])


@router.get("/announcements")
async def get_announcements():
    """Return recent login announcements."""
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("login_announcements")
            .select("id,title,content,created_at")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
    except Exception as e:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to fetch announcements") from e

    rows = getattr(res, "data", res) or []
    data = [
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "content": r.get("content"),
            "created_at": r.get("created_at"),
        }
        for r in rows
    ]
    return {"announcements": data}


class EventPayload(BaseModel):
    event: str


@router.post("/event")
async def log_login_event(
    payload: EventPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Record a login related event for auditing."""
    log_action(db, user_id, "login_event", payload.event)
    return {"message": "event logged"}
