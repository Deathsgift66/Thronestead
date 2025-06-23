# Project Name: Thronestead©
# File Name: spies_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: spies_router.py
Role: API routes for spies router.
Version: 2025-06-21
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services import spies_service

from ..database import get_db
from ..security import verify_jwt_token
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/kingdom", tags=["spies"])


# -------------------- Request Payloads --------------------


class SpyMissionPayload(BaseModel):
    mission: Optional[str] = Field(
        None, description="Alias for mission_type for backward compatibility"
    )
    mission_type: Optional[str] = Field(None, description="Type of mission to launch")
    target_id: Optional[int] = Field(
        None, description="Target kingdom ID for the spy mission"
    )


class TrainPayload(BaseModel):
    quantity: int = Field(
        ..., gt=0, le=100, description="Number of spies to train (1-100 max per call)"
    )


# -------------------- Spy Routes --------------------


@router.get("/spies")
def get_spy_info(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
) -> dict:
    """Return the player's spy count and training info."""
    kid = get_kingdom_id(db, user_id)
    try:
        return spies_service.get_spy_record(db, kid)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load spy data") from e


@router.post("/spies/train")
def train_spies(
    payload: TrainPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Train a number of spies for the kingdom."""
    kid = get_kingdom_id(db, user_id)
    try:
        new_count = spies_service.train_spies(db, kid, payload.quantity)
        return {"spy_count": new_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to train spies") from e


@router.post("/spy_missions")
def launch_spy_mission(
    payload: SpyMissionPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Start a new spy mission."""
    kid = get_kingdom_id(db, user_id)
    mtype = payload.mission_type or payload.mission
    if not mtype:
        raise HTTPException(status_code=400, detail="mission_type is required")

    try:
        spies_service.start_mission(db, kid, payload.target_id)
        mission_id = spies_service.create_spy_mission(db, kid, mtype, payload.target_id)
        return {"message": "Mission launched", "mission_id": mission_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to launch spy mission"
        ) from e


@router.get("/spy_missions")
def list_spy_missions(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
) -> dict:
    """Return all spy missions currently active for the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    try:
        missions = spies_service.list_spy_missions(db, kid)
        return {"missions": missions}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to load spy missions"
        ) from e
