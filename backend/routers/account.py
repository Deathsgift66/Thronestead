# Project Name: Thronestead©
# File Name: account.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""
Project: Thronestead ©
File: account.py
Role: API routes for account management.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from services.moderation import validate_clean_text
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
    if value is not None:
        validate_clean_text(value)
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

    changes = payload.dict(exclude_none=True)
    if not changes:
        return {"message": "no changes"}

    assignments = ", ".join(f"{f} = :{f}" for f in changes)
    db.execute(
        text(f"UPDATE users SET {assignments} WHERE user_id = :uid"),
        {"uid": user_id, **changes},
    )
    db.commit()
    log_action(db, user_id, "update_account", ",".join(changes))
    return {"message": "updated"}
