# Project Name: Thronestead©
# File Name: login_routes.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: login_routes.py
Role: API routes for login routes.
Version: 2025-06-21
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from services.audit_service import log_action

from ..database import get_db
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client
from ..rate_limiter import limiter

router = APIRouter(prefix="/api/login", tags=["login"])


@router.get("/announcements", response_class=JSONResponse)
def get_announcements():
    """
    🔔 Fetch the 10 most recent public login screen announcements.

    Returns:
        - List of announcement dicts with 'title', 'content', and 'created_at'.
    """
    try:
        supabase = get_supabase_client()
    except RuntimeError as exc:
        logging.exception("Supabase client unavailable")
        raise HTTPException(status_code=503, detail="Supabase unavailable") from exc

    try:
        response = (
            supabase.table("announcements")
            .select("title,content,created_at")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        if getattr(response, "status_code", 200) >= 400:
            raise ValueError("Invalid Supabase response")

        announcements = getattr(response, "data", response) or []
    except Exception as e:
        logging.exception("Error loading announcements")
        raise HTTPException(
            status_code=500, detail="Server error loading announcements."
        ) from e
    return JSONResponse(content={"announcements": announcements}, status_code=200)


class EventPayload(BaseModel):
    event: str


@router.post("/event")
@limiter.limit("5/minute")
def log_login_event(
    request: Request,
    payload: EventPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    📘 Log user login-related actions (e.g., successful login, login attempt).

    Parameters:
        - payload.event (str): Description of the login event

    Returns:
        - Success message after recording the event
    """
    log_action(db, user_id, "login_event", payload.event)
    return {"message": "event logged"}


@router.get("/status")
def login_status(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return the user's onboarding completion flag."""
    row = db.execute(
        text("SELECT setup_complete FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    complete = bool(row[0]) if row else False
    return {"setup_complete": complete}
