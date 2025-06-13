# Project Name: Kingmakers Rise©
# File Name: training_history.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import get_db
from services.training_history_service import record_training, fetch_history

router = APIRouter(prefix="/api/training-history", tags=["training_history"])


class TrainingPayload(BaseModel):
    kingdom_id: int
    unit_id: int
    unit_name: str
    quantity: int
    source: str
    initiated_at: datetime
    trained_by: str | None = None
    xp_awarded: int = 0
    modifiers_applied: dict | None = None


@router.get("")
def get_history(
    kingdom_id: int = Query(...),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    records = fetch_history(db, kingdom_id, limit)
    return {"history": records}


@router.post("")
def create_history(payload: TrainingPayload, db: Session = Depends(get_db)):
    hid = record_training(
        db,
        kingdom_id=payload.kingdom_id,
        unit_id=payload.unit_id,
        unit_name=payload.unit_name,
        quantity=payload.quantity,
        source=payload.source,
        initiated_at=payload.initiated_at,
        trained_by=payload.trained_by,
        xp_awarded=payload.xp_awarded,
        modifiers_applied=payload.modifiers_applied or {},
    )
    return {"history_id": hid}
