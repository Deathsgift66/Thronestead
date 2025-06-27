# Project Name: Thronestead©
# File Name: reauth.py
# Version: 6.14.2025
# Developer: Codex
"""Project: Thronestead ©
File: reauth.py
Role: API route for user re-authentication prior to sensitive actions.
Version: 2025-06-21
"""

from __future__ import annotations

import os
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from ..database import get_db
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------------------------------------------
# Configuration + In-memory Stores
# ---------------------------------------------
_reauth_ttl = os.getenv("REAUTH_TOKEN_TTL")
TOKEN_TTL = int(_reauth_ttl) if _reauth_ttl else 300  # 5 minutes
_lockout_env = os.getenv("REAUTH_LOCKOUT_THRESHOLD")
LOCKOUT_THRESHOLD = int(_lockout_env) if _lockout_env else 5

REAUTH_TOKENS: dict[str, float] = {}  # user_id: expiry
FAILED_ATTEMPTS: dict[tuple[str, str], tuple[int, float]] = {}  # (uid, ip): (count, expiry)


class ReauthPayload(BaseModel):
    password: str


def _prune_expired() -> None:
    now = time.time()
    for uid, exp in list(REAUTH_TOKENS.items()):
        if exp <= now:
            REAUTH_TOKENS.pop(uid, None)
    for key, (count, exp) in list(FAILED_ATTEMPTS.items()):
        if exp <= now:
            FAILED_ATTEMPTS.pop(key, None)


@router.post("/reauth")
def reauthenticate(
    payload: ReauthPayload,
    request: Request,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Validate the user's password and issue a short-lived re-auth token."""
    _prune_expired()
    ip = request.client.host if request.client else ""
    key = (user_id, ip)
    record = FAILED_ATTEMPTS.get(key)
    if record and record[0] >= LOCKOUT_THRESHOLD and record[1] > time.time():
        raise HTTPException(status_code=429, detail="Too many re-auth attempts")

    email = db.execute(
        text("SELECT email FROM users WHERE user_id = :uid"), {"uid": user_id}
    ).scalar()
    if not email:
        raise HTTPException(status_code=404, detail="User not found")

    sb = get_supabase_client()
    try:
        result = sb.auth.sign_in_with_password({"email": email, "password": payload.password})
    except Exception as exc:  # pragma: no cover - network/dependency issues
        raise HTTPException(status_code=500, detail="Authentication service error") from exc

    if isinstance(result, dict):
        error = result.get("error")
    else:
        error = getattr(result, "error", None)

    if error:
        count, _ = FAILED_ATTEMPTS.get(key, (0, 0))
        FAILED_ATTEMPTS[key] = (count + 1, time.time() + TOKEN_TTL)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    REAUTH_TOKENS[user_id] = time.time() + TOKEN_TTL
    FAILED_ATTEMPTS.pop(key, None)
    return {"reauthenticated": True}
