# Project Name: Thronestead©
# File Name: signup.py
# Version:  7/1/2025 10:38
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
from pydantic import BaseModel, EmailStr, constr, validator
from services.moderation import (
    validate_clean_text,
    validate_username,
    validate_kingdom_name,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import Kingdom, Notification
from services.resource_service import ensure_kingdom_resource_row

from ..database import get_db
from ..supabase_client import get_supabase_client
from ..rate_limiter import limiter
from fastapi import Request, Header
from services.audit_service import log_action
import httpx
from ..env_utils import get_env_var
from ..security import verify_jwt_token

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
    """Raise :class:`HTTPException` if the username already exists."""
    row = db.execute(
        text("SELECT 1 FROM users WHERE lower(username) = lower(:u)"),
        {"u": username},
    ).fetchone()
    if row:
        raise HTTPException(status_code=400, detail="Username already taken")


def _check_kingdom_free(db: Session, name: str) -> None:
    """Raise :class:`HTTPException` if the kingdom name already exists."""
    row = db.execute(
        text("SELECT 1 FROM kingdoms WHERE lower(kingdom_name) = lower(:n)"),
        {"n": name},
    ).fetchone()
    if row:
        raise HTTPException(status_code=400, detail="Kingdom name already taken")


def _check_email_free(db: Session, email: str) -> None:
    """Raise :class:`HTTPException` if the email address already exists."""
    row = db.execute(
        text("SELECT 1 FROM users WHERE lower(email) = lower(:e)"),
        {"e": email},
    ).fetchone()
    if row:
        raise HTTPException(status_code=400, detail="Email already registered")


# ------------- Payload Models -------------------


class CheckPayload(BaseModel):
    display_name: Optional[str] = None
    username: Optional[constr(min_length=3, max_length=20)] = None
    email: Optional[EmailStr] = None

    _check_display = validator("display_name", allow_reuse=True)(
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

    _check_display = validator(
        "display_name",
        "kingdom_name",
        allow_reuse=True,
    )(lambda v: _validate_text(v))
    _check_username = validator("username", allow_reuse=True)(
        lambda v: _validate_username(v)
    )


class RegisterPayload(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=6)] = None
    username: constr(min_length=3, max_length=20)
    kingdom_name: str
    display_name: str
    region: str
    profile_bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    captcha_token: Optional[str] = None
    user_id: Optional[str] = None

    _check_display = validator(
        "display_name",
        allow_reuse=True,
    )(lambda v: _validate_text(v))
    _check_kingdom = validator("kingdom_name", allow_reuse=True)(
        lambda v: _validate_kingdom_name(v)
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


def _validate_kingdom_name(value: str | None) -> str | None:
    if value is not None:
        validate_kingdom_name(value)
    return value


# ------------- Route Endpoints -------------------


@router.post("/check")
def check_availability(
    payload: CheckPayload, db: Session = Depends(get_db)
):
    """Return availability for usernames, emails, and display names."""
    if not (payload.username or payload.display_name or payload.email):
        raise HTTPException(status_code=400, detail="Missing required fields")
    username_available = True
    email_available = True
    display_available = True

    if payload.username:
        row = db.execute(
            text("SELECT 1 FROM users WHERE lower(username) = lower(:u)"),
            {"u": payload.username},
        ).fetchone()
        username_available = row is None

    if payload.email:
        row = db.execute(
            text("SELECT 1 FROM users WHERE lower(email) = lower(:e)"),
            {"e": payload.email},
        ).fetchone()
        email_available = row is None

    if payload.display_name:
        row = db.execute(
            text("SELECT 1 FROM users WHERE lower(display_name) = lower(:d)"),
            {"d": payload.display_name},
        ).fetchone()
        display_available = row is None

    return {
        "username_available": username_available,
        "email_available": email_available,
        "display_available": display_available,
    }


@router.get("/check")
def check_kingdom_name(kingdom: str, db: Session = Depends(get_db)):
    """Check if the provided kingdom name is available."""
    row = db.execute(
        text("SELECT 1 FROM kingdoms WHERE lower(kingdom_name) = lower(:n)"),
        {"n": kingdom},
    ).fetchone()
    return {"available": row is None}


@router.get("/available")
def available(
    kingdom_name: str | None = None,
    email: str | None = None,
    db: Session = Depends(get_db),
):
    """Check if a kingdom name or email address is already taken."""
    if not kingdom_name and not email:
        raise HTTPException(status_code=400, detail="Missing parameters")

    if kingdom_name:
        row = db.execute(
            text(
                "SELECT 1 FROM kingdoms WHERE lower(kingdom_name) = lower(:n)"
            ),
            {"n": kingdom_name},
        ).fetchone()
        if row:
            return {"available": False}

    if email:
        row = db.execute(
            text("SELECT 1 FROM users WHERE lower(email) = lower(:e)"),
            {"e": email},
        ).fetchone()
        if row:
            return {"available": False}

    return {"available": True}


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
    _check_email_free(db, payload.email)
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
    _check_email_free(db, payload.email)

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
            {"uid": payload.user_id},
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
        return {"status": "created", "user_id": payload.user_id, "kingdom_id": kid}
    except Exception as exc:
        logger.exception("Failed to finalize signup")
        raise HTTPException(status_code=500, detail="Failed to finalize signup") from exc


@router.post("/register")
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: RegisterPayload,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
):
    """
    Create a Supabase auth user and register their kingdom profile.
    """
    sb = get_supabase_client()

    # --- CSRF/Token Verification ---
    if authorization:
        token_uid = verify_jwt_token(authorization=authorization)
        if payload.user_id and payload.user_id != token_uid:
            raise HTTPException(status_code=400, detail="User ID mismatch")
        if not payload.user_id:
            payload.user_id = token_uid

    validate_kingdom_name(payload.kingdom_name)

    # --- Uniqueness Checks ---
    _check_username_free(db, payload.username)
    _check_email_free(db, payload.email)

    _check_kingdom_free(db, payload.kingdom_name)

    row = db.execute(
        text("SELECT region_name FROM region_catalogue WHERE region_code = :c"),
        {"c": payload.region},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid region")
    region_name = row[0]



    # --- hCaptcha Verification ---
    if not verify_hcaptcha(payload.captcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    uid = payload.user_id
    confirmed = True
    user_obj = None
    created_auth_user = False

    if uid is None:
        try:
            res = sb.auth.sign_up(
                {
                    "email": payload.email,
                    "password": payload.password,
                    "options": {
                        "emailRedirectTo": "https://www.thronestead.com/login.html",
                        "data": {
                            "display_name": payload.display_name,
                            "username": payload.username,
                        },
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
        # Allow account creation to proceed even if email is not yet confirmed

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

        created_auth_user = True

    try:
        db.execute(
            text(
                """
                INSERT INTO users (user_id, username, display_name, kingdom_name, email, auth_user_id, sign_up_ip, region, profile_bio, profile_picture_url)
                VALUES (:uid, :username, :display, :kingdom, :email, :uid, :ip, :region, :bio, :pic)
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
                "region": region_name,
                "bio": payload.profile_bio,
                "pic": payload.profile_picture_url,
            },
        )

        kid = None
        if confirmed:
            row = db.execute(
                text(
                    """
                    INSERT INTO kingdoms (user_id, kingdom_name, ruler_name, region)
                    VALUES (:uid, :kingdom, :display, :region)
                    RETURNING kingdom_id
                    """
                ),
                {
                    "uid": uid,
                    "kingdom": payload.kingdom_name,
                    "display": payload.display_name,
                    "region": region_name,
                },
            ).fetchone()
            kid = int(row[0]) if row else None

            if kid:
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
        if created_auth_user:
            try:
                admin = getattr(sb.auth, "admin", sb.auth)
                if hasattr(admin, "delete_user"):
                    admin.delete_user(uid)
            except Exception:
                logger.warning("Failed to delete Supabase user %s", uid)
        raise HTTPException(
            status_code=500, detail="Failed to save user profile"
        ) from exc
    if not confirmed:
        try:
            sb.auth.resend({
                "type": "signup",
                "email": payload.email,
                "emailRedirectTo": "https://www.thronestead.com/login.html",
            })
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
    user_info = None
    try:
        admin = getattr(sb.auth, "admin", None)
        if admin and hasattr(admin, "get_user_by_email"):
            user_info = admin.get_user_by_email(payload.email)
    except Exception:  # pragma: no cover - network/dependency issues
        logger.exception("Failed to look up user before resend")
        # Fall back to resending without confirmation check

    user = (
        user_info.get("user") if isinstance(user_info, dict) else getattr(user_info, "user", None)
    ) or user_info
    confirmed = bool(
        user
        and (
            getattr(user, "confirmed_at", None)
            or getattr(user, "email_confirmed_at", None)
            or (isinstance(user, dict) and user.get("confirmed_at"))
            or (isinstance(user, dict) and user.get("email_confirmed_at"))
        )
    )
    if confirmed:
        return {"status": "already_verified"}

    try:
        res = sb.auth.resend({
            "type": "signup",
            "email": payload.email,
            "emailRedirectTo": "https://www.thronestead.com/login.html",
        })
    except Exception as exc:
        logger.exception("Failed to resend confirmation email")
        raise HTTPException(status_code=500, detail="Failed to resend email") from exc

    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(
            status_code=400, detail=res["error"].get("message", "Resend failed")
        )

    return {"status": "sent"}
