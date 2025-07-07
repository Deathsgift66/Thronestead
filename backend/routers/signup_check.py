# Project Name: Thronestead©
# File Name: signup_check.py
# Version: 7.5.2025.21.01
# Developer: Codex

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
    username = (payload.username or "").strip().lower()
    display_name = (payload.display_name or "").strip().lower()
    email = (payload.email or "").strip().lower()

    if not username and not email:
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        user_row = db.execute(
            text("SELECT 1 FROM users WHERE LOWER(TRIM(username)) = :name OR LOWER(TRIM(display_name)) = :name LIMIT 1"),
            {"name": username},
        ).fetchone()

        kingdom_row = db.execute(
            text("SELECT 1 FROM kingdoms WHERE LOWER(TRIM(kingdom_name)) = :name OR LOWER(TRIM(ruler_name)) = :name LIMIT 1"),
            {"name": username},
        ).fetchone()

        username_taken = user_row is not None or kingdom_row is not None

        # Check if email exists in users table
        email_result = db.execute(
            text("""
                SELECT 1 FROM users WHERE LOWER(TRIM(email)) = :email LIMIT 1;
            """),
            {"email": email}
        ).fetchone()

        email_taken = email_result is not None

        # Optional: Check Supabase auth.users metadata (if synced with DB)
        try:
            supabase_result = db.execute(
                text("""
                    SELECT 1 FROM auth.users
                    WHERE LOWER(TRIM(raw_user_meta_data->>'display_name')) = :username
                       OR LOWER(TRIM(raw_user_meta_data->>'username')) = :username
                       OR LOWER(TRIM(email)) = :email
                    LIMIT 1;
                """),
                {"username": username, "email": email}
            ).fetchone()
            if supabase_result:
                username_taken = True
                email_taken = True
        except Exception as e:
            logger.warning("Supabase auth.users check failed: %s", e)

        return {
            "username_available": not username_taken,
            "email_available": not email_taken
        }

    except Exception as e:
        logger.error("Error during signup availability check: %s", e)
        raise HTTPException(status_code=500, detail="Failed to check availability")
