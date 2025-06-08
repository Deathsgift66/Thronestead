from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from services.kingdom_history_service import log_event, fetch_history
from pydantic import BaseModel

router = APIRouter(prefix="/api/kingdom-history", tags=["kingdom_history"])


class HistoryPayload(BaseModel):
    kingdom_id: int
    event_type: str
    event_details: str


@router.get("")
def history(
    kingdom_id: int = Query(...),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return recent history for a kingdom."""
    records = fetch_history(db, kingdom_id, limit)
    return {"history": records}


@router.post("")
def create_history(payload: HistoryPayload, db: Session = Depends(get_db)):
    """Insert a new history event."""
    log_event(db, payload.kingdom_id, payload.event_type, payload.event_details)
    return {"message": "logged"}
