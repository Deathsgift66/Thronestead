# Project Name: Thronestead©
# File Name: auth.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Unified authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .forgot_password import (
    EmailPayload,
    CodePayload,
    PasswordPayload,
    request_password_reset as _request_password_reset,
    verify_reset_code as _verify_reset_code,
    set_new_password as _set_new_password,
)
from .session import validate_session as _validate_session
from .signup import ResendPayload, resend_confirmation as _resend_confirmation
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/request-password-reset", status_code=status.HTTP_201_CREATED)
def request_password_reset(
    payload: EmailPayload, request: Request, db: Session = Depends(get_db)
):
    """Wrapper for forgot_password.request_password_reset."""
    return _request_password_reset(payload, request, db)


@router.post("/verify-reset-code")
def verify_reset_code(payload: CodePayload, request: Request):
    """Wrapper for forgot_password.verify_reset_code."""
    return _verify_reset_code(payload, request)


@router.post("/set-new-password")
def set_new_password(
    payload: PasswordPayload, request: Request, db: Session = Depends(get_db)
):
    """Wrapper for forgot_password.set_new_password."""
    return _set_new_password(payload, db, request)


@router.get("/validate-session")
async def validate_session(request: Request):
    """Wrapper for session.validate_session."""
    return await _validate_session(request)


@router.post("/resend-confirmation")
def resend_confirmation(payload: ResendPayload):
    """Resend the signup confirmation email."""
    return _resend_confirmation(payload)
