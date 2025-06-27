# Project Name: Thronestead©
# File Name: forgot_password.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: forgot_password.py
Role: API routes for forgot password.
Version: 2025-06-21
"""

import hashlib
import logging
import os
import re
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from backend.models import Notification, User
from services.audit_service import log_action

from ..database import get_db
from ..supabase_client import get_supabase_client
from services.email_service import send_email


router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------------------------------------------
# Configuration + In-memory Stores
# ---------------------------------------------
RESET_STORE: dict[str, tuple[str, float]] = {}  # token_hash: (user_id, expiry)
VERIFIED_SESSIONS: dict[str, tuple[str, float]] = {}  # user_id: (token_hash, expiry)
RATE_LIMIT: dict[str, list[float]] = {}  # IP: [timestamps]

_token_ttl = os.getenv("PASSWORD_RESET_TOKEN_TTL")
TOKEN_TTL = int(_token_ttl) if _token_ttl else 900  # 15 minutes
_session_ttl = os.getenv("PASSWORD_RESET_SESSION_TTL")
SESSION_TTL = int(_session_ttl) if _session_ttl else 600  # 10 minutes
_rate_limit = os.getenv("PASSWORD_RESET_RATE_LIMIT")
RATE_LIMIT_MAX = int(_rate_limit) if _rate_limit else 3  # 3 per hour


# ---------------------------------------------
# Payload Models
# ---------------------------------------------
class EmailPayload(BaseModel):
    email: EmailStr


class CodePayload(BaseModel):
    code: str


class PasswordPayload(BaseModel):
    code: str
    new_password: str
    confirm_password: str


# ---------------------------------------------
# Helper Functions
# ---------------------------------------------
def _prune_expired() -> None:
    """Remove expired tokens, sessions, and prune old IP rate entries."""
    now = time.time()
    for key, (_, expiry) in list(RESET_STORE.items()):
        if expiry <= now:
            RESET_STORE.pop(key, None)

    for uid, (_, expiry) in list(VERIFIED_SESSIONS.items()):
        if expiry <= now:
            VERIFIED_SESSIONS.pop(uid, None)

    for ip in list(RATE_LIMIT.keys()):
        RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < 3600]
        if not RATE_LIMIT[ip]:
            RATE_LIMIT.pop(ip)


def _hash_token(token: str) -> str:
    """Securely hash the token using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------
# Route: Request Password Reset
# ---------------------------------------------
@router.post("/request-password-reset", status_code=status.HTTP_201_CREATED)
def request_password_reset(
    payload: EmailPayload, request: Request, db: Session = Depends(get_db)
):
    _prune_expired()
    ip = request.client.host if request.client else ""
    history = RATE_LIMIT.setdefault(ip, [])
    if len(history) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many requests")
    history.append(time.time())

    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = uuid.uuid4().hex
        token_hash = _hash_token(token)
        RESET_STORE[token_hash] = (str(user.user_id), time.time() + TOKEN_TTL)

        send_email(user.email, subject="Reset Code", body=token)
        logging.getLogger("Thronestead.PasswordReset").info(
            "Password reset token generated for %s", user.email
        )

    return {"message": "If the email exists, a reset link has been sent."}


# ---------------------------------------------
# Route: Verify Reset Code
# ---------------------------------------------
@router.post("/verify-reset-code")
def verify_reset_code(payload: CodePayload):
    _prune_expired()
    token_hash = _hash_token(payload.code)
    record = RESET_STORE.get(token_hash)
    if not record or record[1] < time.time():
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    uid = record[0]
    VERIFIED_SESSIONS[uid] = (token_hash, time.time() + SESSION_TTL)
    return {"message": "verified"}


# ---------------------------------------------
# Route: Set New Password
# ---------------------------------------------
@router.post("/set-new-password")
def set_new_password(payload: PasswordPayload, db: Session = Depends(get_db)):
    _prune_expired()

    token_hash = _hash_token(payload.code)
    record = RESET_STORE.get(token_hash)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    uid = record[0]
    session = VERIFIED_SESSIONS.get(uid)
    if not session or session[0] != token_hash or session[1] < time.time():
        raise HTTPException(status_code=400, detail="Reset session expired")

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password mismatch")

    if len(payload.new_password) < 12 or not (
        re.search(r"[A-Z]", payload.new_password)
        and re.search(r"[a-z]", payload.new_password)
        and re.search(r"[0-9]", payload.new_password)
    ):
        raise HTTPException(status_code=400, detail="Password too weak")

    try:
        sb = get_supabase_client()
        sb.auth.admin.update_user_by_id(uid, {"password": payload.new_password})
    except Exception as exc:  # pragma: no cover - runtime dependency
        logging.getLogger("Thronestead.PasswordReset").exception(
            "Failed to update password for user %s", uid
        )
        raise HTTPException(status_code=500, detail="Password update failed") from exc

    db.execute(
        text("UPDATE users SET updated_at = now() WHERE user_id = :uid"), {"uid": uid}
    )

    log_action(
        db, uid, "password_reset", f"Password successfully reset for user: {uid}"
    )

    db.add(
        Notification(
            user_id=uid,
            title="Password Reset Confirmed",
            message="Your password has been securely changed. If this wasn't you, contact support.",
            priority="high",
            category="security",
            link_action="/login.html",
        )
    )
    db.commit()

    RESET_STORE.pop(token_hash, None)
    VERIFIED_SESSIONS.pop(uid, None)

    return {"message": "password updated"}
