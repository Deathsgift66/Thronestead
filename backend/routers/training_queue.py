from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..security import verify_jwt_token
from ..database import get_db
from .progression_router import get_kingdom_id
from services.training_queue_service import (
    add_training_order,
    fetch_queue,
    cancel_training,
)

router = APIRouter(prefix="/api/training_queue", tags=["training_queue"])


class TrainOrderPayload(BaseModel):
    unit_id: int
    unit_name: str
    quantity: int
    base_training_seconds: int = 60


class CancelPayload(BaseModel):
    queue_id: int


@router.post("/start")
def start_training(
    payload: TrainOrderPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    qid = add_training_order(
        db,
        kingdom_id=kid,
        unit_id=payload.unit_id,
        unit_name=payload.unit_name,
        quantity=payload.quantity,
        base_training_seconds=payload.base_training_seconds,
    )
    return {"queue_id": qid}


@router.get("")
def list_queue(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    rows = fetch_queue(db, kid)
    return {"queue": rows}


@router.post("/cancel")
def cancel_order(
    payload: CancelPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    cancel_training(db, payload.queue_id, kid)
    return {"message": "Training cancelled"}

