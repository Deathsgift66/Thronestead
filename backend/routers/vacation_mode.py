# Project Name: Thronestead©
# File Name: vacation_mode.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

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

# Define the API route group
router = APIRouter(prefix="/api/vacation", tags=["vacation"])

@router.post("/enter", summary="Enable Vacation Mode")
def enter_vm(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Enables Vacation Mode for the user's kingdom. This protects their kingdom
    from actions and disables gameplay features until exited.
    """
    # Resolve kingdom ID from user
    kid = get_kingdom_id(db, user_id)

    # Call service to enter vacation mode and return expiry
    expires = enter_vacation_mode(db, kid)

    return {"message": "Vacation Mode enabled", "expires_at": expires}


@router.post("/exit", summary="Disable Vacation Mode")
def exit_vm(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Exits Vacation Mode for the user's kingdom, if eligible.
    """
    # Resolve kingdom ID from user
    kid = get_kingdom_id(db, user_id)

    # Verify if user is allowed to exit vacation mode (minimum period enforced)
    if not can_exit_vacation(db, kid):
        raise HTTPException(status_code=403, detail="Vacation period not over")

    # Exit vacation mode via service
    exit_vacation_mode(db, kid)

    return {"message": "Vacation Mode disabled"}
