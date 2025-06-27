# Project Name: Thronestead©
# File Name: account_delete.py
# Version 6.15.2025
# Developer: OpenAI Codex
"""
Project: Thronestead ©
File: account_delete.py
Role: API route for user account deletion.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/account", tags=["account"])


@router.delete("/delete")
def delete_account(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Soft delete a user account and redact profile fields."""
    exists = db.execute(
        text("SELECT 1 FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    db.execute(
        text(
            """
            UPDATE users
               SET is_deleted = true,
                   display_name = NULL,
                   profile_picture_url = NULL,
                   profile_bio = NULL,
                   auth_user_id = NULL
             WHERE user_id = :uid
            """
        ),
        {"uid": user_id},
    )
    db.commit()
    log_action(db, user_id, "delete_account", "")
    return {"status": "deleted"}
