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
import time
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from services.audit_service import log_action
from services.notification_service import notify_new_login

from ..database import get_db
from ..security import verify_jwt_token, has_active_ban
from ..supabase_client import get_supabase_client
from ..rate_limiter import limiter

router = APIRouter(prefix="/api/login", tags=["login"])

from ..env_utils import get_env

ALLOW_UNVERIFIED_LOGIN = (
    get_env("ALLOW_UNVERIFIED_LOGIN", default="false").lower() == "true"
)


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


class AttemptPayload(BaseModel):
    email: EmailStr
    success: bool


class ErrorContextPayload(BaseModel):
    email: EmailStr | None = None
    message: str
    timestamp: float
    user_agent: str | None = None
    platform: str | None = None


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
    ip = request.headers.get("x-forwarded-for")
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    if not ip:
        ip = request.client.host if request.client else ""
    agent = request.headers.get("user-agent", "")
    log_action(db, user_id, "login_event", payload.event, ip, agent)
    return {"message": "event logged"}


@router.post("/attempt")
@limiter.limit("20/minute")
def record_login_attempt(request: Request, payload: AttemptPayload, db: Session = Depends(get_db)):
    """Record a login attempt success or failure."""
    try:
        row = db.execute(
            text("SELECT user_id FROM users WHERE lower(email)=:email"),
            {"email": payload.email.lower()},
        ).fetchone()
        user_id = row[0] if row else None
        action = "login_success" if payload.success else "login_fail"
        ip = request.headers.get("x-forwarded-for")
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        if not ip:
            ip = request.client.host if request.client else ""
        agent = request.headers.get("user-agent", "")
        log_action(db, user_id, action, payload.email.lower(), ip, agent)
        return {"logged": True}
    except Exception:
        logging.exception("Failed to record login attempt")
        return {"logged": False}


@router.post("/error-context")
@limiter.limit("20/minute")
def log_error_context(request: Request, payload: ErrorContextPayload, db: Session = Depends(get_db)) -> dict:
    """Record client-side login error details."""
    try:
        user_id = None
        if payload.email:
            row = db.execute(
                text("SELECT user_id FROM users WHERE lower(email)=:email"),
                {"email": payload.email.lower()},
            ).fetchone()
            user_id = row[0] if row else None
        ip = request.headers.get("x-forwarded-for")
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        if not ip:
            ip = request.client.host if request.client else ""
        agent = payload.user_agent or request.headers.get("user-agent", "")
        details = (
            f"{payload.message} | ts={payload.timestamp} | platform={payload.platform}"
        )
        log_action(db, user_id, "login_error", details, ip, agent)
        return {"logged": True}
    except Exception:
        logging.exception("Failed to record login error context")
        return {"logged": False}


@router.get("/status")
def login_status(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return the user's onboarding completion flag."""
    db.execute(
        text("UPDATE users SET last_login_at = now() WHERE user_id = :uid"),
        {"uid": user_id},
    )
    db.commit()
    row = db.execute(
        text("SELECT setup_complete FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    complete = bool(row[0]) if row else False
    return {"setup_complete": complete}


FAILED_LOGINS: dict[tuple[str, str], tuple[int, float]] = {}


def _prune_attempts() -> None:
    now = time.time()
    for key, (_, exp) in list(FAILED_LOGINS.items()):
        if exp <= now:
            FAILED_LOGINS.pop(key, None)


class AuthPayload(BaseModel):
    email: EmailStr
    password: str
    otp: str | None = None


@router.post("/authenticate")
def authenticate(
    request: Request,
    payload: AuthPayload,
    db: Session = Depends(get_db),
) -> dict:
    """Validate credentials with Supabase and return session plus profile info."""
    ip = request.headers.get("x-forwarded-for")
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    if not ip:
        ip = request.client.host if request.client else ""
    device_hash = request.headers.get("X-Device-Hash")

    _prune_attempts()
    key = (payload.email.lower(), ip)
    record = FAILED_LOGINS.get(key)
    if record and record[1] > time.time():
        raise HTTPException(status_code=429, detail="Too many failed attempts")

    if has_active_ban(db, ip=ip, device_hash=device_hash):
        raise HTTPException(status_code=403, detail="Access banned")

    sb = get_supabase_client()
    data = {"email": payload.email, "password": payload.password}
    if payload.otp:
        data["otp_token"] = payload.otp
    try:
        res = sb.auth.sign_in_with_password(data)
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
        count, _ = FAILED_LOGINS.get(key, (0, 0))
        delay = min(2 ** count, 300)
        FAILED_LOGINS[key] = (count + 1, time.time() + delay)
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
    if not confirmed and not ALLOW_UNVERIFIED_LOGIN:
        raise HTTPException(status_code=401, detail="Email not confirmed")

    uid = getattr(user, "id", None) or (isinstance(user, dict) and user.get("id"))
    agent = request.headers.get("user-agent", "")
    if has_active_ban(db, user_id=uid, ip=ip, device_hash=device_hash):
        raise HTTPException(status_code=403, detail="Account banned")
    row = db.execute(
        text(
            "SELECT username, kingdom_id, alliance_id, setup_complete, is_deleted, status "
            "FROM users WHERE user_id = :uid"
        ),
        {"uid": uid},
    ).fetchone()

    username = row[0] if row else None
    kingdom_id = row[1] if row else None
    alliance_id = row[2] if row else None
    setup_complete = bool(row[3]) if row else False
    is_deleted = bool(row[4]) if row else False
    status = row[5] if row else None

    if is_deleted:
        raise HTTPException(status_code=403, detail="Account deleted")
    if status and status.lower() == "suspicious" and not payload.otp:
        raise HTTPException(status_code=401, detail="2FA required")

    db.execute(
        text("UPDATE users SET last_login_at = now() WHERE user_id = :uid"),
        {"uid": uid},
    )
    db.commit()
    FAILED_LOGINS.pop(key, None)
    try:
        notify_new_login(db, uid, ip, agent)
    except Exception:
        pass
    try:  # pragma: no cover - ignore failures
        sb.table("user_active_sessions").insert(
            {"user_id": uid, "ip_address": ip, "device_info": agent}
        ).execute()
    except Exception:
        pass

    return {
        "session": session,
        "username": username,
        "kingdom_id": kingdom_id,
        "alliance_id": alliance_id,
        "setup_complete": setup_complete,
    }


class ReauthPayload(BaseModel):
    password: str
    otp: str | None = None


@router.post("/reauth")
def reauthenticate(
    request: Request,
    payload: ReauthPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Re-authenticate a logged-in user by password (and optional OTP)."""
    ip = request.headers.get("x-forwarded-for")
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    if not ip:
        ip = request.client.host if request.client else ""
    device_hash = request.headers.get("X-Device-Hash")

    if has_active_ban(db, user_id=user_id, ip=ip, device_hash=device_hash):
        raise HTTPException(status_code=403, detail="Account banned")

    row = db.execute(
        text("SELECT email, status FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    email, status = row

    if status and status.lower() == "suspicious" and not payload.otp:
        raise HTTPException(status_code=401, detail="2FA required")

    sb = get_supabase_client()
    data = {"email": email, "password": payload.password}
    if payload.otp:
        data["otp_token"] = payload.otp
    try:
        res = sb.auth.sign_in_with_password(data)
    except Exception as exc:  # pragma: no cover - network/dependency issues
        raise HTTPException(
            status_code=500, detail="Authentication service error"
        ) from exc

    if isinstance(res, dict):
        error = res.get("error")
        session = res.get("session")
    else:
        error = getattr(res, "error", None)
        session = getattr(res, "session", None)
    if error or not session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"reauthenticated": True}
