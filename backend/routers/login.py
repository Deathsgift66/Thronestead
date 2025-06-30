# Project Name: Thronestead©
# File Name: login.py
# Version 6.14.2025
# Developer: Codex
"""
Project: Thronestead ©
File: login.py
Role: API route providing backend controlled Supabase authentication.
Version: 2025-06-21
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import os

from ..supabase_client import get_supabase_client

router = APIRouter(tags=["login"])

ALLOW_UNVERIFIED_LOGIN = os.getenv("ALLOW_UNVERIFIED_LOGIN", "false").lower() == "true"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/api/login")
def login_user(payload: LoginRequest):
    """Authenticate a user via Supabase and return the response."""
    supabase = get_supabase_client()
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:  # pragma: no cover - network/dependency issues
        raise HTTPException(
            status_code=500, detail="Authentication service error"
        ) from exc

    if isinstance(result, dict):
        error = result.get("error")
        user = result.get("user")
    else:  # Supabase object
        error = getattr(result, "error", None)
        user = getattr(result, "user", None)

    if error:
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

    return result
