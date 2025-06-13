from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..data import global_game_settings, load_game_settings
from ..database import get_db
from .progression_router import get_user_id

router = APIRouter(prefix="/api", tags=["settings"])

@router.get("/game/settings")
async def get_settings() -> dict:
    """Return the currently loaded game settings."""
    return global_game_settings

class SettingPayload(BaseModel):
    key: str
    value: Any
    is_active: bool = True

@router.post("/admin/game_settings")
async def update_setting(
    payload: SettingPayload,
    admin_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Update a game setting and reload the in-memory cache."""
    db.execute(
        text(
            """
            UPDATE game_settings
            SET setting_value = :val,
                is_active = :active,
                last_updated = NOW(),
                updated_by = :uid
            WHERE setting_key = :key
            """
        ),
        {
            "val": payload.value,
            "active": payload.is_active,
            "uid": admin_id,
            "key": payload.key,
        },
    )
    db.commit()
    load_game_settings()
    return {"message": "Setting updated"}

