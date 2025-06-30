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
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, constr, validator
from services.moderation import validate_clean_text, validate_username
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import Kingdom, Notification
from services.resource_service import ensure_kingdom_resource_row

from ..database import get_db
from ..supabase_client import get_supabase_client
from ..rate_limiter import limiter
from fastapi import Request
from services.audit_service import log_action
import httpx
from ..env_utils import get_env_var

HCAPTCHA_SECRET = get_env_var("HCAPTCHA_SECRET")


def verify_hcaptcha(token: str | None, remote_ip: str | None = None) -> bool:
    """Validate the hCaptcha token if configured."""
    if not HCAPTCHA_SECRET:
        # Captcha not configured; treat as always valid
        return True
    if not token:
        return False
    try:
        data = {"secret": HCAPTCHA_SECRET, "response": token}
        if remote_ip:
            data["remoteip"] = remote_ip
        resp = httpx.post(
            "https://hcaptcha.com/siteverify", data=data, timeout=5
        )
        resp.raise_for_status()
        result = resp.json()
        return bool(result.get("success"))
    except Exception:  # pragma: no cover - external call
        logger.exception("hCaptcha verification failed")
        return False

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

    _check_kingdom = validator("kingdom_name", allow_reuse=True)(
        lambda v: _validate_text(v)
    )
    _check_username = validator("username", allow_reuse=True)(
        lambda v: _validate_username(v)
    )


class CreateUserPayload(BaseModel):
    user_id: str
    username: str
    display_name: str
    kingdom_name: str
    email: EmailStr

    _check_display = validator("display_name", "kingdom_name", allow_reuse=True)(
        lambda v: _validate_text(v)
    )
    _check_username = validator("username", allow_reuse=True)(
        lambda v: _validate_username(v)
    )


class RegisterPayload(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=6)] = None
    username: constr(min_length=3, max_length=20)
    kingdom_name: str
    display_name: str
    captcha_token: Optional[str] = None
    user_id: Optional[str] = None

    _check_display = validator("display_name", "kingdom_name", allow_reuse=True)(
        lambda v: _validate_text(v)
    )
    _check_username = validator("username", allow_reuse=True)(
        lambda v: _validate_username(v)
    )


class ResendPayload(BaseModel):
    email: EmailStr


def _validate_text(value: str | None) -> str | None:
    if value is not None:
        validate_clean_text(value)
    return value


def _validate_username(value: str | None) -> str | None:
    if value is not None:
        validate_username(value)
    return value


# ------------- Route Endpoints -------------------


@router.post("/check")
def check_availability(
    payload: CheckPayload, db: Session = Depends(get_db)
):
    """
    Check if a kingdom name or username is available.
    """
    try:
        sb = get_supabase_client()
    except Exception:  # pragma: no cover - service might be down
        logger.warning("Supabase client unavailable; falling back to DB")
        sb = None
    available_kingdom = True
    available_username = True
    available_email = True

    def _query_db() -> None:
        nonlocal available_kingdom, available_username, available_email
        if payload.kingdom_name:
            row = db.execute(
                text("SELECT 1 FROM kingdoms WHERE kingdom_name = :n LIMIT 1"),
                {"n": payload.kingdom_name},
            ).fetchone()
            available_kingdom = row is None

        if payload.username:
            row = db.execute(
                text("SELECT 1 FROM users WHERE username = :u LIMIT 1"),
                {"u": payload.username},
            ).fetchone()
            available_username = row is None

        if payload.email:
            row = db.execute(
                text("SELECT 1 FROM users WHERE email = :e LIMIT 1"),
                {"e": payload.email},
            ).fetchone()
            available_email = row is None

    if sb:
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
        except Exception:  # pragma: no cover - supabase failure
            logger.warning("Supabase query failed; falling back to DB")
            sb = None

    if not sb:
        try:
            _query_db()
        except Exception as exc:  # pragma: no cover - unexpected DB failure
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
def signup_stats(db: Session = Depends(get_db)):
    """Return top kingdoms for display on the signup screen."""
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("leaderboard_kingdoms")
            .select("kingdom_name,score")
            .order("score", desc=True)
            .limit(3)
            .execute()
        )
        data = getattr(res, "data", res) or []
        if data:
            return {"top_kingdoms": data}
    except Exception:  # pragma: no cover - fall back to DB query
        import traceback

        logger.error("Error in /api/signup/stats:\n%s", traceback.format_exc())

    rows = (
        db.query(Kingdom.kingdom_name, Kingdom.prestige_score.label("score"))
        .order_by(Kingdom.prestige_score.desc())
        .limit(3)
        .all()
    )
    data = [
        {"kingdom_name": r.kingdom_name, "score": r.score or 0} for r in rows
    ]
    return {"top_kingdoms": data}


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

    # --- hCaptcha Verification ---
    if not verify_hcaptcha(payload.captcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=400, detail="Captcha verification failed")

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

        village = db.execute(
            text(
                """
                INSERT INTO kingdom_villages (kingdom_id, village_name, village_type)
                VALUES (:kid, :name, 'capital')
                RETURNING village_id
                """
            ),
            {"kid": kid, "name": payload.kingdom_name},
        ).fetchone()
        if village:
            db.execute(
                text(
                    "INSERT INTO village_buildings (village_id, building_id, level) "
                    "VALUES (:vid, 1, 1) ON CONFLICT DO NOTHING"
                ),
                {"vid": int(village[0])},
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
        agent = request.headers.get("user-agent", "")
        ip = request.client.host if request.client else None
        log_action(db, uid, "signup", f"User {uid} registered", ip, agent)
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
