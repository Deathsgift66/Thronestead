from __future__ import annotations
import hashlib
import os
import time
import uuid
import re
from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from pydantic import BaseModel

from ..database import get_db
from backend.models import User, Notification
from services.audit_service import log_action

router = APIRouter(prefix="/api/auth", tags=["auth"])

RESET_STORE: dict[str, tuple[str, float]] = {}
VERIFIED_SESSIONS: dict[str, tuple[str, float]] = {}
RATE_LIMIT: dict[str, list[float]] = {}
TOKEN_TTL = int(os.getenv("PASSWORD_RESET_TOKEN_TTL", "900"))
SESSION_TTL = int(os.getenv("PASSWORD_RESET_SESSION_TTL", "600"))
RATE_LIMIT_MAX = int(os.getenv("PASSWORD_RESET_RATE_LIMIT", "3"))

class EmailPayload(BaseModel):
    email: str

class CodePayload(BaseModel):
    code: str

class PasswordPayload(BaseModel):
    code: str
    new_password: str
    confirm_password: str


def _prune_expired() -> None:
    now = time.time()
    for token, (_, exp) in list(RESET_STORE.items()):
        if exp < now:
            RESET_STORE.pop(token, None)
    for uid, (_, exp) in list(VERIFIED_SESSIONS.items()):
        if exp < now:
            VERIFIED_SESSIONS.pop(uid, None)
    for ip, times in list(RATE_LIMIT.items()):
        RATE_LIMIT[ip] = [t for t in times if now - t < 3600]


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


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
        # Here we would send an email with the unhashed token
    # Always respond success
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/verify-reset-code")
def verify_reset_code(payload: CodePayload):
    _prune_expired()
    token_hash = _hash_token(payload.code)
    record = RESET_STORE.get(token_hash)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    uid, exp = record
    if exp < time.time():
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    VERIFIED_SESSIONS[uid] = (token_hash, time.time() + SESSION_TTL)
    return {"message": "verified"}


@router.post("/set-new-password")
def set_new_password(payload: PasswordPayload, db: Session = Depends(get_db)):
    _prune_expired()
    token_hash = _hash_token(payload.code)
    record = RESET_STORE.get(token_hash)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    uid, _ = record
    session = VERIFIED_SESSIONS.get(uid)
    if not session or session[0] != token_hash:
        raise HTTPException(status_code=400, detail="Reset session expired")
    if session[1] < time.time():
        VERIFIED_SESSIONS.pop(uid, None)
        raise HTTPException(status_code=400, detail="Reset session expired")
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password mismatch")
    if len(payload.new_password) < 12 or not (
        re.search(r"[A-Z]", payload.new_password)
        and re.search(r"[a-z]", payload.new_password)
        and re.search(r"[0-9]", payload.new_password)
    ):
        raise HTTPException(status_code=400, detail="Password too weak")

    db.execute(text("UPDATE users SET updated_at = now() WHERE user_id = :uid"), {"uid": uid})
    log_action(db, uid, "password_reset", f"Password successfully reset for user: {uid}")
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
