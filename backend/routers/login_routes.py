from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.audit_service import log_action


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/login", tags=["login"])


@router.get("/announcements", response_class=JSONResponse)
def get_announcements():
    """Return the latest public announcements for the login screen."""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("announcements")
            .select("title,content,created_at")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
    except Exception as e:  # pragma: no cover - network/db errors
        print("❌ Error loading announcements:", e)
        raise HTTPException(status_code=500, detail="Server error loading announcements.") from e

    if getattr(res, "status_code", 200) >= 400:
        raise HTTPException(status_code=500, detail="Failed to fetch announcements.")

    announcements = getattr(res, "data", res) or []

    return JSONResponse(content=announcements, status_code=200)


class EventPayload(BaseModel):
    event: str


@router.post("/event")
def log_login_event(
    payload: EventPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Record a login related event for auditing."""
    log_action(db, user_id, "login_event", payload.event)
    return {"message": "event logged"}
