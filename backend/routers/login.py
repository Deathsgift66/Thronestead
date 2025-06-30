"""Backend controlled Supabase authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..env_utils import get_env_var, strtobool
from ..supabase_client import get_supabase_client
from ..database import get_db
from services.system_flag_service import get_flag

router = APIRouter(tags=["login"])

ALLOW_UNVERIFIED_LOGIN = bool(
    strtobool(get_env_var("ALLOW_UNVERIFIED_LOGIN", default="false"))
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/api/login")
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user via Supabase and return the response."""
    if get_flag(db, "maintenance_mode") or get_flag(db, "fallback_override"):
        raise HTTPException(status_code=503, detail="Login disabled")

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
