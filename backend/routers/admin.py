from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id
from services.audit_service import log_action

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PlayerAction(BaseModel):
    player_id: str
    alert_id: str | None = None


class BulkAction(BaseModel):
    action: str
    player_ids: list[str]


@router.post("/flag")
async def flag_player(
    payload: PlayerAction,
    admin_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "flag_user", f"Flagged user {payload.player_id}")
    return {"message": "Flagged", "player_id": payload.player_id}


@router.post("/freeze")
async def freeze_player(
    payload: PlayerAction,
    admin_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "freeze_user", f"Froze user {payload.player_id}")
    return {"message": "Frozen", "player_id": payload.player_id}


@router.post("/ban")
async def ban_player(
    payload: PlayerAction,
    admin_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "ban_user", f"Banned user {payload.player_id}")
    return {"message": "Banned", "player_id": payload.player_id}


@router.get("/players")
async def list_players(search: str | None = None):
    return {"players": [], "search": search}


@router.post("/bulk_action")
async def bulk_action(
    payload: BulkAction,
    admin_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    log_action(
        db,
        admin_id,
        "bulk_admin_action",
        f"{payload.action} on {len(payload.player_ids)} players",
    )
    return {"message": "Bulk action executed", "action": payload.action}


@router.post("/player_action")
async def player_action(
    payload: PlayerAction,
    admin_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "admin_action", payload.alert_id or "")
    return {"message": "Action executed", "action": payload.alert_id}

