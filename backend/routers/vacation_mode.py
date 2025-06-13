from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id
from services.vacation_mode_service import (
    enter_vacation_mode,
    exit_vacation_mode,
    can_exit_vacation,
)

router = APIRouter(prefix="/api/vacation", tags=["vacation"])


@router.post("/enter")
def enter_vm(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    expires = enter_vacation_mode(db, kid)
    return {"message": "Vacation Mode enabled", "expires_at": expires}


@router.post("/exit")
def exit_vm(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    if not can_exit_vacation(db, kid):
        raise HTTPException(status_code=403, detail="Vacation period not over")
    exit_vacation_mode(db, kid)
    return {"message": "Vacation Mode disabled"}
