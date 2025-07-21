# Project Name: Thronestead©
# File Name: reauth.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""
Project: Thronestead ©
File: reauth.py
Role: API route for generating reauth tokens.
Version: 2025-07-21
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import (
    create_reauth_token,
    has_active_ban,
    verify_jwt_token,
    _extract_request_meta,
)
from ..supabase_client import get_supabase_client, maybe_await

router = APIRouter(prefix="/api", tags=["auth"])


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
    """Re-authenticate a logged-in user by password and optional OTP."""
    ip, device_hash = _extract_request_meta(request)
    if has_active_ban(db, user_id=user_id, ip=ip, device_hash=device_hash):
        raise HTTPException(status_code=403, detail="Account banned")

    row = db.execute(
        text("SELECT email FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    email = row[0]

    try:
        sb = get_supabase_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Supabase unavailable") from exc

    data = {"email": email, "password": payload.password}
    if payload.otp:
        data["otp_token"] = payload.otp
    try:
        res = maybe_await(sb.auth.sign_in_with_password(data))
    except Exception as exc:  # pragma: no cover - network failure
        raise HTTPException(status_code=500, detail="Authentication service error") from exc

    if isinstance(res, dict):
        error = res.get("error")
        session = res.get("session")
    else:
        error = getattr(res, "error", None)
        session = getattr(res, "session", None)
    if error or not session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_reauth_token(db, user_id, ttl=300)
    return {"token": token, "expires_in": 300}
