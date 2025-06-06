from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PlayerAction(BaseModel):
    player_id: str
    alert_id: str | None = None


class BulkAction(BaseModel):
    action: str
    player_ids: list[str]


@router.post("/flag")
async def flag_player(payload: PlayerAction):
    return {"message": "Flagged", "player_id": payload.player_id}


@router.post("/freeze")
async def freeze_player(payload: PlayerAction):
    return {"message": "Frozen", "player_id": payload.player_id}


@router.post("/ban")
async def ban_player(payload: PlayerAction):
    return {"message": "Banned", "player_id": payload.player_id}


@router.get("/players")
async def list_players(search: str | None = None):
    return {"players": [], "search": search}


@router.post("/bulk_action")
async def bulk_action(payload: BulkAction):
    return {"message": "Bulk action executed", "action": payload.action}


@router.post("/player_action")
async def player_action(payload: PlayerAction):
    return {"message": "Action executed", "action": payload.alert_id}

