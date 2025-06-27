from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from services.audit_service import log_action

from ..database import get_db
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/reauth", tags=["reauth"])

TOKEN_TTL = int(os.getenv("REAUTH_TOKEN_TTL", "300"))


class ReauthPayload(BaseModel):
    password: str
    code: str | None = None


@router.post("")
def reauthenticate(
    payload: ReauthPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Validate credentials again and issue a short-lived re-auth token."""
    row = db.execute(text("SELECT email FROM users WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    email = row[0]

    sb = get_supabase_client()
    try:
        res = sb.auth.sign_in_with_password({"email": email, "password": payload.password})
    except Exception as exc:  # pragma: no cover - external failure
        log_action(db, user_id, "reauth_fail", "service_error")
        raise HTTPException(status_code=500, detail="Authentication service error") from exc

    error = getattr(res, "error", None)
    session = getattr(res, "session", None)
    if isinstance(res, dict):
        error = res.get("error")
        session = res.get("session")
    if error or not session:
        log_action(db, user_id, "reauth_fail", "invalid_credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if payload.code:
        try:
            verify = sb.auth.verify_otp({"email": email, "token": payload.code, "type": "totp"})
            if isinstance(verify, dict) and verify.get("error"):
                raise ValueError("Invalid 2FA")
        except Exception as exc:
            log_action(db, user_id, "reauth_fail", "invalid_2fa")
            raise HTTPException(status_code=401, detail="Invalid 2FA code") from exc

    token = uuid.uuid4().hex
    expires = datetime.utcnow() + timedelta(seconds=TOKEN_TTL)
    db.execute(
        text(
            """
            INSERT INTO reauth_tokens (token, user_id, expires_at)
            VALUES (:tok, :uid, :exp)
            """
        ),
        {"tok": token, "uid": user_id, "exp": expires},
    )
    db.commit()

    log_action(db, user_id, "reauth_success", "")
    return {"token": token, "expires": expires.isoformat()}
