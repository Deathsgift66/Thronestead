from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from services.kingdom_history_service import (
    log_event,
    fetch_history,
    fetch_full_history,
)
from .progression_router import get_kingdom_id
from .admin_dashboard import verify_admin
from ..security import verify_jwt_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/kingdom-history", tags=["kingdom_history"])


class HistoryPayload(BaseModel):
    kingdom_id: int
    event_type: str
    event_details: str


@router.get("")

def kingdom_history(
    kingdom_id: int = Query(...),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return recent history for a kingdom."""
    records = fetch_history(db, kingdom_id, limit)
    return {"history": records}



@router.post("")
def create_history(
    payload: HistoryPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Insert a new history event."""

    log_event(db, payload.kingdom_id, payload.event_type, payload.event_details)
    return {"message": "logged"}


@router.get("/{kingdom_id}/full")
def full_history(
    kingdom_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return all historical data for the requested kingdom."""

    try:
        player_kid = get_kingdom_id(db, user_id)
    except HTTPException:
        player_kid = None

    if player_kid != kingdom_id:
        try:
            verify_admin(user_id, db)
        except HTTPException:
            raise HTTPException(status_code=403, detail="Access denied")

    data = fetch_full_history(db, kingdom_id)
    return data
