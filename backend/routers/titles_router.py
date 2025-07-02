# Project Name: Thronestead©
# File Name: titles_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: titles_router.py
Role: API routes for titles router.
Version: 2025-06-21
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.kingdom_title_service import award_title, list_titles, set_active_title

from ..data import prestige_scores
from ..database import get_db
from ..security import require_user_id, verify_api_key
from .progression_router import get_kingdom_id
from ..security import verify_admin

router = APIRouter(prefix="/api/kingdom", tags=["titles"])


# ---------------------- Payload Models ----------------------


class TitlePayload(BaseModel):
    title: str = Field(
        ..., min_length=2, max_length=100, description="The name of the title to award"
    )


class ActiveTitlePayload(BaseModel):
    title: Optional[str] = Field(
        None, description="The title to set as active (or null to clear)"
    )


# ---------------------- Endpoints ----------------------


@router.get("/titles", summary="List Kingdom Titles")
async def list_titles_endpoint(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """List all titles awarded to the player's kingdom."""
    kingdom_id = get_kingdom_id(db, user_id)
    titles = list_titles(db, kingdom_id)
    return {"titles": titles}


@router.post("/titles", summary="Award Title to Kingdom")
def award_title_endpoint(
    payload: TitlePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(None),
) -> dict:
    """Award a title to the player's kingdom."""

    # Only admins or internal events (via API key) may award titles
    if x_api_key:
        verify_api_key(x_api_key)
    else:
        try:
            verify_admin(user_id, db)
        except HTTPException:
            raise HTTPException(status_code=403, detail="Admin access required")

    kingdom_id = get_kingdom_id(db, user_id)
    try:
        award_title(db, kingdom_id, payload.title)
        return {"message": "Title awarded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to award title") from e


@router.post("/active_title", summary="Set Active Kingdom Title")
def set_active_title_endpoint(
    payload: ActiveTitlePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Set or clear the active title displayed for the kingdom."""
    kingdom_id = get_kingdom_id(db, user_id)
    try:
        set_active_title(db, kingdom_id, payload.title)
        return {"message": "Active title updated"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to update active title"
        ) from e


@router.get("/prestige", summary="Get Prestige Score")
async def get_prestige(user_id: str = Depends(require_user_id)) -> dict:
    """Return the current prestige score for the user."""
    return {"prestige_score": prestige_scores.get(user_id, 0)}
