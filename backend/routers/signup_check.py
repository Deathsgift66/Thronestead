# Project Name: Thronestead©
# File Name: signup_check.py
# Version: 7.5.2025.21.01
# Developer: Codex

"""Utility route for checking signup data availability."""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class SignupCheckRequest(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None

@router.post("/api/signup/check")
async def check_signup_availability(
    payload: SignupCheckRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Return availability flags for provided signup fields."""

    if not (payload.username or payload.display_name or payload.email):
        raise HTTPException(status_code=400, detail="Missing required fields")

    result = {
        "username_available": True,
        "email_available": True,
        "display_available": True,
    }

    if payload.username:
        row = db.execute(
            text("SELECT 1 FROM users WHERE lower(username) = lower(:u)"),
            {"u": payload.username},
        ).fetchone()
        result["username_available"] = row is None

    if payload.email:
        row = db.execute(
            text("SELECT 1 FROM users WHERE lower(email) = lower(:e)"),
            {"e": payload.email},
        ).fetchone()
        result["email_available"] = row is None

    if payload.display_name:
        row = db.execute(
            text("SELECT 1 FROM users WHERE lower(display_name) = lower(:d)"),
            {"d": payload.display_name},
        ).fetchone()
        result["display_available"] = row is None

    return result
