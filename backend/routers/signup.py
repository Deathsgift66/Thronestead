# Project Name: Thronestead©
# File Name: signup.py
# Version 6.15.2025.21.00
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: signup.py
Role: API routes for signup.
Version: 2025-06-21
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import Notification
from services.resource_service import ensure_kingdom_resource_row

from ..database import get_db
from ..supabase_client import get_supabase_client
from ..rate_limiter import limiter
from fastapi import Request
from services.audit_service import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signup", tags=["signup"])


def _check_username_free(db: Session, username: str) -> None:
    """Raise 409 if the username already exists."""
    count = db.execute(
        text("SELECT COUNT(*) FROM users WHERE username = :u"),
        {"u": username},
    ).scalar()
    if count:
        raise HTTPException(status_code=409, detail="Username already exists")


def _check_kingdom_free(db: Session, name: str) -> None:
    """Raise 409 if the kingdom name already exists."""
    count = db.execute(
        text("SELECT COUNT(*) FROM kingdoms WHERE kingdom_name = :n"),
        {"n": name},
    ).scalar()
    if count:
        raise HTTPException(status_code=409, detail="Kingdom name already exists")


# ------------- Payload Models -------------------


class CheckPayload(BaseModel):
    kingdom_name: Optional[str] = None
    username: Optional[constr(min_length=3, max_length=20)] = None
    email: Optional[EmailStr] = None


class CreateUserPayload(BaseModel):
    user_id: str
    username: str
    display_name: str
    kingdom_name: str
    email: EmailStr


class RegisterPayload(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=6)] = None
    username: constr(min_length=3, max_length=20)
    kingdom_name: str
    display_name: str
    captcha_token: Optional[str] = None
    user_id: Optional[str] = None


class ResendPayload(BaseModel):
    email: EmailStr


# ------------- Route Endpoints -------------------


@router.post("/check")
def check_availability(payload: CheckPayload):
    """
    Check if a kingdom name or username is available.
    """
    sb = get_supabase_client()
    available_kingdom = True
    available_username = True
    available_email = True

    try:
        if payload.kingdom_name:
            res = (
                sb.table("kingdoms")
                .select("kingdom_id")
                .eq("kingdom_name", payload.kingdom_name)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", res) or []
            available_kingdom = len(rows) == 0

        if payload.username:
            res = (
                sb.table("users")
                .select("id")
                .eq("username", payload.username)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", res) or []
            available_username = len(rows) == 0

        if payload.email:
            res = (
                sb.table("users")
                .select("id")
                .eq("email", payload.email)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", res) or []
            available_email = len(rows) == 0

    except Exception as exc:
        logger.exception("Failed to query availability")
        raise HTTPException(
            status_code=500, detail="Failed to query availability"
        ) from exc

    return {
        "kingdom_available": available_kingdom,
        "username_available": available_username,
        "email_available": available_email,
    }


@router.get("/check")
def check_kingdom_name(kingdom: str):
    """Return whether the provided kingdom name is available."""
    sb = get_supabase_client()
    try:
        res = (
            sb.table("kingdoms")
            .select("kingdom_id")
            .eq("kingdom_name", kingdom)
            .limit(1)
            .execute()
        )
        rows = getattr(res, "data", res) or []
        available = len(rows) == 0
    except Exception as exc:
        logger.exception("Failed to query availability")
        raise HTTPException(
            status_code=500, detail="Failed to query availability"
        ) from exc
    return {"available": available}


@router.get("/stats")
def signup_stats():
    """
    Return top kingdoms for display on the signup screen.
    """
    sb = get_supabase_client()
    try:
        res = (
            sb.table("leaderboard_kingdoms")
            .select("kingdom_name,score")
            .order("score", desc=True)
            .limit(3)
            .execute()
        )
        data = getattr(res, "data", res) or []
        return {"top_kingdoms": data}
    except Exception as exc:
        logger.exception("Failed to fetch kingdom stats")
        raise HTTPException(
            status_code=500, detail="Failed to fetch kingdom stats"
        ) from exc


@router.post("/create_user")
def create_user(payload: CreateUserPayload, db: Session = Depends(get_db)):
    """
    Create the user's basic profile record after authentication setup.
    """
    _check_username_free(db, payload.username)
    _check_kingdom_free(db, payload.kingdom_name)
    try:
        db.execute(
            text(
                """
                INSERT INTO users (user_id, username, display_name, kingdom_name, email)
                VALUES (:uid, :username, :display, :kingdom, :email)
                ON CONFLICT (user_id) DO NOTHING
                """
            ),
            {
                "uid": payload.user_id,
                "username": payload.username,
                "display": payload.display_name,
                "kingdom": payload.kingdom_name,
                "email": payload.email,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO user_setting_entries (user_id, setting_key, setting_value)
                VALUES (:uid, 'theme', 'default')
                ON CONFLICT DO NOTHING
                """
            ),
            {"uid": payload.user_id},
        )

        db.add(
            Notification(
                user_id=payload.user_id,
                title="Welcome to Thronestead!",
                message="Your kingdom awaits.",
                category="system",
            )
        )

        db.commit()
        return {"status": "created"}
    except Exception as e:
        logger.exception("Failed to create user")
        raise HTTPException(status_code=500, detail="Failed to create user") from e


class FinalizePayload(BaseModel):
    """Payload for :func:`finalize_signup`."""

    user_id: str
    username: str
    display_name: str
    kingdom_name: str
    email: EmailStr


@router.post("/finalize")
def finalize_signup(payload: FinalizePayload, db: Session = Depends(get_db)):
    """Finalize signup after Supabase user creation."""

    if not payload.user_id or len(payload.user_id) < 6:
        raise HTTPException(status_code=400, detail="Invalid user id")

    _check_username_free(db, payload.username)
    _check_kingdom_free(db, payload.kingdom_name)

    try:
        db.execute(
            text(
                """
                INSERT INTO users (user_id, username, display_name, kingdom_name, email, auth_user_id)
                VALUES (:uid, :username, :display, :kingdom, :email, :uid)
                ON CONFLICT (user_id) DO NOTHING
                """
            ),
            {
                "uid": payload.user_id,
                "username": payload.username,
                "display": payload.display_name,
                "kingdom": payload.kingdom_name,
                "email": payload.email,
            },
        )

        row = db.execute(
            text(
                """
                INSERT INTO kingdoms (user_id, kingdom_name, ruler_name)
                VALUES (:uid, :kingdom, :display)
                RETURNING kingdom_id
                """
            ),
            {
                "uid": payload.user_id,
                "kingdom": payload.kingdom_name,
                "display": payload.display_name,
            },
        ).fetchone()
        kid = int(row[0]) if row else None

        ensure_kingdom_resource_row(db, kid)
        db.execute(
            text("INSERT INTO kingdom_titles (kingdom_id, title) VALUES (:kid, 'Founder')"),
            {"kid": kid},
        )

        db.commit()
        return {"status": "created", "user_id": payload.user_id, "kingdom_id": kid}
    except Exception as exc:
        logger.exception("Failed to finalize signup")
        raise HTTPException(status_code=500, detail="Failed to finalize signup") from exc


@router.post("/register")
@limiter.limit("5/minute")
def register(
    request: Request, payload: RegisterPayload, db: Session = Depends(get_db)
):
    """
    Create a Supabase auth user and register their kingdom profile.
    """
    sb = get_supabase_client()

    # --- Uniqueness Checks ---
    _check_username_free(db, payload.username)
    count_email = db.execute(
        text("SELECT COUNT(*) FROM users WHERE email = :e"),
        {"e": payload.email},
    ).scalar()
    if count_email:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    _check_kingdom_free(db, payload.kingdom_name)

    if not payload.username.isalnum():
        raise HTTPException(status_code=400, detail="Username must be alphanumeric")

    uid = payload.user_id
    confirmed = True
    user_obj = None

    if uid is None:
        try:
            res = sb.auth.sign_up(
                {
                    "email": payload.email,
                    "password": payload.password,
                    "options": {
                        "data": {
                            "display_name": payload.display_name,
                            "username": payload.username,
                        }
                    },
                }
            )
        except Exception as exc:
            logger.exception("❌ Failed to create auth user")
            raise HTTPException(
                status_code=500, detail="Internal server error during signup."
            ) from exc

        if isinstance(res, dict) and res.get("error"):
            logger.error("Supabase signup error: %s", res["error"])
            raise HTTPException(
                status_code=400, detail=res["error"].get("message", "Signup failed")
            )

        # Require email confirmation before proceeding
        user_obj = getattr(res, "user", None)
        if user_obj is None and isinstance(res, dict):
            user_obj = res.get("user")
        confirmed_at = None
        if user_obj:
            confirmed_at = getattr(user_obj, "confirmed_at", None) or user_obj.get(
                "confirmed_at"
            )
        if not confirmed_at:
            raise HTTPException(
                status_code=202,
                detail="Please confirm your email address before logging in.",
            )

        # Extract the newly created user ID
        if user_obj:
            uid = getattr(user_obj, "id", None) or user_obj.get("id")
        if uid is None:
            uid = getattr(res, "id", None) or (isinstance(res, dict) and res.get("id"))

        confirmed = bool(
            getattr(user_obj, "confirmed_at", None)
            or getattr(user_obj, "email_confirmed_at", None)
            or (isinstance(user_obj, dict) and user_obj.get("email_confirmed_at"))
        )

        if not uid:
            raise HTTPException(status_code=500, detail="Signup failed - user ID missing")

    try:
        db.execute(
            text(
                """
                INSERT INTO users (user_id, username, display_name, kingdom_name, email, auth_user_id, sign_up_ip)
                VALUES (:uid, :username, :display, :kingdom, :email, :uid, :ip)
                ON CONFLICT (user_id) DO NOTHING
                """
            ),
            {
                "uid": uid,
                "username": payload.username,
                "display": payload.display_name,
                "kingdom": payload.kingdom_name,
                "email": payload.email,
                "ip": request.client.host if request.client else None,
            },
        )

        row = db.execute(
            text(
                """
                INSERT INTO kingdoms (user_id, kingdom_name, ruler_name)
                VALUES (:uid, :kingdom, :display)
                RETURNING kingdom_id
                """
            ),
            {
                "uid": uid,
                "kingdom": payload.kingdom_name,
                "display": payload.display_name,
            },
        ).fetchone()
        kid = int(row[0]) if row else None

        ensure_kingdom_resource_row(db, kid)
        db.execute(
            text("INSERT INTO kingdom_titles (kingdom_id, title) VALUES (:kid, 'Founder')"),
            {"kid": kid},
        )

        db.execute(
            text(
                "INSERT INTO kingdom_vip_status (user_id, vip_level) VALUES (:uid, 0) ON CONFLICT (user_id) DO NOTHING"
            ),
            {"uid": uid},
        )

        db.execute(
            text(
                """
                INSERT INTO user_setting_entries (user_id, setting_key, setting_value)
                VALUES (:uid, 'theme', 'default')
                ON CONFLICT DO NOTHING
                """
            ),
            {"uid": uid},
        )

        db.add(
            Notification(
                user_id=uid,
                title="Welcome to Thronestead!",
                message="Your kingdom awaits.",
                category="system",
            )
        )

        db.commit()
        log_action(db, uid, "signup", f"User {uid} registered")
    except Exception as exc:
        logger.exception("Failed to save user profile")
        raise HTTPException(
            status_code=500, detail="Failed to save user profile"
        ) from exc
    if not confirmed:
        try:
            sb.auth.resend({"type": "signup", "email": payload.email})
        except Exception:
            logger.warning("Failed to trigger confirmation email for %s", payload.email)

    return {
        "user_id": uid,
        "kingdom_id": kid,
        "email_confirmation_required": not confirmed,
    }


@router.post("/resend-confirmation")
def resend_confirmation(payload: ResendPayload):
    """Resend the signup confirmation email."""
    sb = get_supabase_client()
    try:
        res = sb.auth.resend({"type": "signup", "email": payload.email})
    except Exception as exc:
        logger.exception("Failed to resend confirmation email")
        raise HTTPException(status_code=500, detail="Failed to resend email") from exc

    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(
            status_code=400, detail=res["error"].get("message", "Resend failed")
        )

    return {"status": "sent"}
