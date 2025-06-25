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
from pydantic import BaseModel, EmailStr
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
    db.execute(
        text("UPDATE users SET last_login_at = now() WHERE user_id = :uid"),
        {"uid": user_id},
    )
    row = db.execute(
        text("SELECT setup_complete FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    complete = bool(row[0]) if row else False
    return {"setup_complete": complete}


class AuthPayload(BaseModel):
    email: EmailStr
    password: str


@router.post("/authenticate")
def authenticate(
    payload: AuthPayload, db: Session = Depends(get_db)
) -> dict:
    """Validate credentials with Supabase and return session plus profile info."""
    sb = get_supabase_client()
    try:
        res = sb.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:  # pragma: no cover - network/dependency issues
        raise HTTPException(
            status_code=500, detail="Authentication service error"
        ) from exc

    if isinstance(res, dict):
        error = res.get("error")
        session = res.get("session")
        user = res.get("user")
    else:
        error = getattr(res, "error", None)
        session = getattr(res, "session", None)
        user = getattr(res, "user", None)

    if error or not session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    confirmed = bool(
        user
        and (
            getattr(user, "confirmed_at", None)
            or getattr(user, "email_confirmed_at", None)
            or (isinstance(user, dict) and user.get("confirmed_at"))
            or (isinstance(user, dict) and user.get("email_confirmed_at"))
        )
    )
    if not confirmed:
        raise HTTPException(status_code=401, detail="Email not confirmed")

    uid = getattr(user, "id", None) or (isinstance(user, dict) and user.get("id"))
    db.execute(
        text("UPDATE users SET last_login_at = now() WHERE user_id = :uid"),
        {"uid": uid},
    )
    row = db.execute(
        text(
            "SELECT username, kingdom_id, alliance_id, setup_complete FROM users WHERE user_id = :uid"
        ),
        {"uid": uid},
    ).fetchone()

    username = row[0] if row else None
    kingdom_id = row[1] if row else None
    alliance_id = row[2] if row else None
    setup_complete = bool(row[3]) if row else False

    return {
        "session": session,
        "username": username,
        "kingdom_id": kingdom_id,
        "alliance_id": alliance_id,
        "setup_complete": setup_complete,
    }
