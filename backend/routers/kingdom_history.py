# Project Name: Thronestead©
# File Name: kingdom_history.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: kingdom_history.py
Role: API routes for kingdom history.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.kingdom_history_service import (
    fetch_full_history,
    fetch_history,
    log_event,
)

from ..database import get_db
from ..security import verify_jwt_token
from .admin_dashboard import verify_admin
from .progression_router import get_kingdom_id

# API Router configuration
router = APIRouter(prefix="/api/kingdom-history", tags=["kingdom_history"])


class HistoryPayload(BaseModel):
    kingdom_id: int
    event_type: str
    event_details: str


@router.get("")
def kingdom_history(
    kingdom_id: int = Query(..., description="Kingdom ID to fetch history for"),
    limit: int = Query(
        50, le=500, description="Limit number of records returned (max 500)"
    ),
    db: Session = Depends(get_db),
):
    """
    🔍 Fetch recent kingdom history events.
    """
    records = fetch_history(db, kingdom_id, limit)
    return {"history": records}


@router.post("")
def create_history(
    payload: HistoryPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    🛠 Log a new event into the kingdom's history.

    Typically used for system or developer-level activity logging.
    """
    log_event(db, payload.kingdom_id, payload.event_type, payload.event_details)
    return {"message": "logged"}


@router.get("/{kingdom_id}/full")
def full_history(
    kingdom_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    📜 Retrieve the full history log for a specific kingdom.
    Only the kingdom owner or an admin can access this endpoint.
    """
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
    # Return the aggregated dictionary directly so the frontend
    # can access keys like `timeline` without extra nesting.
    return data
