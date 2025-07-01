# Comment
# Project Name: Thronestead©
# File Name: settings_router.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: settings_router.py
Role: API routes for settings router.
Version: 2025-06-21
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..data import global_game_settings, load_game_settings
from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api", tags=["settings"])


class SettingPayload(BaseModel):
    key: str  # Unique game setting key
    value: Any  # Updated value (any type supported by the setting)
    is_active: bool = True  # Activation flag for the setting


@router.get("/game/settings")
def get_settings() -> dict:
    """
    Public endpoint to retrieve currently loaded game settings.

    Returns:
        Dictionary of key-value pairs from the global game settings cache.
    """
    return global_game_settings


@router.post("/admin/game_settings")
def update_setting(
    payload: SettingPayload,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """
    Admin endpoint to update a game setting and reload the global in-memory cache.

    Args:
        payload (SettingPayload): Contains the setting key, value, and active state.
        admin_id (str): Injected user ID of the admin (authorization required).
        db (Session): Active SQLAlchemy session.

    Returns:
        dict: A confirmation message if the update succeeds.
    """
    try:
        result = db.execute(
            text(
                """
                UPDATE game_settings
                SET is_active = :active,
                    last_updated = NOW(),
                    updated_by = :uid
                WHERE setting_key = :key
                """
            ),
            {
                "active": payload.is_active,
                "uid": admin_id,
                "key": payload.key,
            },
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Setting key not found")

        db.execute(
            text(
                """
                INSERT INTO game_setting_values (setting_key, setting_value)
                VALUES (:key, :val)
                ON CONFLICT (setting_key) DO UPDATE
                SET setting_value = EXCLUDED.setting_value
                """
            ),
            {"key": payload.key, "val": payload.value},
        )

        db.commit()
        load_game_settings()

        return {
            "message": "Setting updated",
            "key": payload.key,
            "new_value": payload.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update setting") from e
