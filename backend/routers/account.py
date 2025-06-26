# Project Name: Thronestead©
# File Name: account.py
# Version 6.14.2025
# Developer: OpenAI Codex
"""
Project: Thronestead ©
File: account.py
Role: API routes for account management.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from services.text_utils import contains_banned_words
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/account", tags=["account"])


class AccountUpdatePayload(BaseModel):
    display_name: str | None = None
    profile_picture_url: str | None = None
    profile_bio: str | None = None

    _check_display = validator("display_name", "profile_bio", allow_reuse=True)(
        lambda v: _validate_text(v)
    )


def _validate_text(value: str | None) -> str | None:
    if value and contains_banned_words(value):
        raise ValueError("Input contains banned words")
    return value


@router.post("/update")
def update_account(
    payload: AccountUpdatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Update user account details like display name and avatar."""
    exists = db.execute(
        text("SELECT 1 FROM users WHERE user_id = :uid"), {"uid": user_id}
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates: list[str] = []
    params = {"uid": user_id}
    field_map = {
        "display_name": "display_name",
        "profile_picture_url": "profile_picture_url",
        "profile_bio": "profile_bio",
    }

    for attr, column in field_map.items():
        value = getattr(payload, attr)
        if value is not None:
            updates.append(f"{column} = :{attr}")
            params[attr] = value

    if updates:
        db.execute(
            text(f"UPDATE users SET {', '.join(updates)} WHERE user_id = :uid"),
            params,
        )
        db.commit()
        log_action(db, user_id, "update_account", ",".join(field_map[k] for k in payload.model_fields_set))
        return {"message": "updated"}

    return {"message": "no changes"}
