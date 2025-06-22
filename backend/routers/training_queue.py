# Project Name: Thronestead©
# File Name: training_queue.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: training_queue.py
Role: API routes for training queue.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..security import verify_jwt_token
from ..database import get_db
from .progression_router import get_kingdom_id
from services.training_queue_service import (
    add_training_order,
    fetch_queue,
    cancel_training,
)
from services.vacation_mode_service import check_vacation_mode

# Router setup
router = APIRouter(prefix="/api/training_queue", tags=["training_queue"])


class TrainOrderPayload(BaseModel):
    """Payload for initiating a training order."""
    unit_id: int = Field(..., description="ID of the unit being trained")
    unit_name: str = Field(..., description="Name of the unit being trained")
    quantity: int = Field(..., gt=0, description="Number of units to train")
    base_training_seconds: int = Field(60, ge=1, description="Base training time per unit in seconds")


class CancelPayload(BaseModel):
    """Payload to cancel a queued training order."""
    queue_id: int = Field(..., description="Queue ID to cancel")


@router.post("/start", summary="Start training", response_description="Queue ID of the training order")
def start_training(
    payload: TrainOrderPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Queue a new training order for the player's kingdom.
    Applies vacation mode check to prevent abuse.
    """
    kingdom_id = get_kingdom_id(db, user_id)
    check_vacation_mode(db, kingdom_id)

    try:
        queue_id = add_training_order(
            db=db,
            kingdom_id=kingdom_id,
            unit_id=payload.unit_id,
            unit_name=payload.unit_name,
            quantity=payload.quantity,
            base_training_seconds=payload.base_training_seconds,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start training order") from e

    return {"queue_id": queue_id}


@router.get("", summary="List training queue", response_description="All active training orders")
def list_queue(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Fetch all active training orders for the authenticated user's kingdom.
    """
    kingdom_id = get_kingdom_id(db, user_id)
    try:
        queue = fetch_queue(db, kingdom_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch training queue") from e

    return {"queue": queue}


@router.post("/cancel", summary="Cancel training order", response_description="Confirmation of cancellation")
def cancel_order(
    payload: CancelPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Cancel a specific training queue order.
    Requires user to not be in vacation mode.
    """
    kingdom_id = get_kingdom_id(db, user_id)
    check_vacation_mode(db, kingdom_id)

    try:
        cancel_training(db, payload.queue_id, kingdom_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cancel training order") from e

    return {"message": "Training cancelled"}
