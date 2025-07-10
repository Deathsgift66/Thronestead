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

    if not username and not display_name and not email:
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        username_taken = False
        email_taken = False
        display_taken = False

        if username:
            user_row = db.execute(
                text(
                    "SELECT 1 FROM users WHERE LOWER(TRIM(username)) = :username LIMIT 1"
                ),
                {"username": username},
            ).fetchone()

            kingdom_row = db.execute(
                text(
                    "SELECT 1 FROM kingdoms "
                    "WHERE LOWER(TRIM(kingdom_name)) = :name "
                    "   OR LOWER(TRIM(ruler_name)) = :name LIMIT 1"
                ),
                {"name": username},
            ).fetchone()

            username_taken = user_row is not None or kingdom_row is not None

        if display_name:
            disp_user_row = db.execute(
                text(
                    "SELECT 1 FROM users WHERE LOWER(TRIM(display_name)) = :name LIMIT 1"
                ),
                {"name": display_name},
            ).fetchone()

            disp_kingdom_row = db.execute(
                text(
                    "SELECT 1 FROM kingdoms "
                    "WHERE LOWER(TRIM(kingdom_name)) = :name "
                    "   OR LOWER(TRIM(ruler_name)) = :name LIMIT 1"
                ),
                {"name": display_name},
            ).fetchone()

            display_taken = disp_user_row is not None or disp_kingdom_row is not None
            username_taken = username_taken or display_taken

        if email:
            email_result = db.execute(
                text(
                    "SELECT email FROM users WHERE LOWER(TRIM(email)) = :email LIMIT 1"
                ),
                {"email": email},
            ).fetchone()

            email_taken = email_result is not None

        # Optional: Check Supabase auth.users metadata (if synced with DB)
        try:
            if username:
                username_row = db.execute(
                    text(
                        "SELECT 1 FROM auth.users "
                        "WHERE LOWER(TRIM(raw_user_meta_data->>'display_name')) = :username "
                        "   OR LOWER(TRIM(raw_user_meta_data->>'username')) = :username "
                        "LIMIT 1;"
                    ),
                    {"username": username},
                ).fetchone()
                if username_row:
                    username_taken = True

            if display_name and not display_taken:
                disp_row = db.execute(
                    text(
                        "SELECT 1 FROM auth.users "
                        "WHERE LOWER(TRIM(raw_user_meta_data->>'display_name')) = :display LIMIT 1;"
                    ),
                    {"display": display_name},
                ).fetchone()
                if disp_row:
                    display_taken = True
                    username_taken = True

            if email:
                email_row = db.execute(
                    text(
                        "SELECT email FROM auth.users WHERE LOWER(TRIM(email)) = :email LIMIT 1"
                    ),
                    {"email": email},
                ).fetchone()
                if email_row:
                    email_taken = True
        except Exception as e:
            logger.warning("Supabase auth.users check failed: %s", e)

        return {
            "username_available": not username_taken,
            "email_available": not email_taken,
            "display_available": not display_taken,
        }

    except Exception as e:
        logger.error("Error during signup availability check: %s", e)
        raise HTTPException(status_code=500, detail="Failed to check availability")
