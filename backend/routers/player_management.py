from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["player_management"])


class BulkAction(BaseModel):
    action: str
    player_ids: list[str]


class PlayerAction(BaseModel):
    action: str
    player_id: str


@router.get("/players")
async def players(search: str | None = None):
    return {"players": [], "search": search}


@router.post("/bulk_action")
async def bulk_action(payload: BulkAction):
    return {"message": "bulk done", "count": len(payload.player_ids)}


@router.post("/player_action")
async def player_action(payload: PlayerAction):
    return {"message": "action done", "player": payload.player_id}

