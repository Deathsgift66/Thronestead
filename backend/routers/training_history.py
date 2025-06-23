# Project Name: Thronestead©
# File Name: training_history.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: training_history.py
Role: API routes for training history.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import get_db
from services.training_history_service import record_training, fetch_history

# Define router prefix and grouping tag
router = APIRouter(prefix="/api/training-history", tags=["training_history"])


class TrainingPayload(BaseModel):
    """Expected structure of a troop training history record."""

    kingdom_id: int = Field(..., description="Kingdom ID performing the training")
    unit_id: int = Field(..., description="ID of the trained unit type")
    unit_name: str = Field(..., description="Name of the trained unit")
    quantity: int = Field(..., gt=0, description="Number of units trained")
    source: str = Field(
        ..., description="Source of training (e.g., 'barracks', 'event')"
    )
    initiated_at: datetime = Field(
        ..., description="Timestamp when training was initiated"
    )
    trained_by: str | None = Field(
        None, description="Trainer's name or admin (optional)"
    )
    modifiers_applied: dict | None = Field(
        default_factory=dict, description="Applied training modifiers"
    )


@router.get(
    "",
    summary="Get training history",
    response_description="List of recent training records",
)
def get_history(
    kingdom_id: int = Query(..., description="Kingdom ID to fetch history for"),
    limit: int = Query(50, ge=1, le=500, description="Max number of entries to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve the most recent troop training history records for a given kingdom.
    """
    try:
        records = fetch_history(db, kingdom_id, limit)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to fetch training history"
        ) from e

    return {"history": records}


@router.post(
    "",
    summary="Record training history",
    response_description="ID of created history record",
)
def create_history(payload: TrainingPayload, db: Session = Depends(get_db)):
    """
    Record a new troop training history event for a given kingdom.
    """
    try:
        history_id = record_training(
            db,
            kingdom_id=payload.kingdom_id,
            unit_id=payload.unit_id,
            unit_name=payload.unit_name,
            quantity=payload.quantity,
            source=payload.source,
            initiated_at=payload.initiated_at,
            trained_by=payload.trained_by,
            modifiers_applied=payload.modifiers_applied or {},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to record training history"
        ) from e

    return {"history_id": history_id}
