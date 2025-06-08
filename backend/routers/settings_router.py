from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..data import global_game_settings

router = APIRouter(prefix="/api", tags=["settings"])

@router.get("/game/settings")
async def get_settings():
    return global_game_settings

class SettingPayload(BaseModel):
    key: str
    value: object

@router.post("/admin/game_settings")
async def update_setting(payload: SettingPayload):
    global_game_settings[payload.key] = payload.value
    return {"message": "Setting updated"}

