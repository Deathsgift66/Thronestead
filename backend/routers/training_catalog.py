# Project Name: Thronestead©
# File Name: training_catalog.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: training_catalog.py
Role: API routes for training catalog.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services.training_catalog_service import list_units

from ..database import get_db
from ..security import verify_jwt_token

# Define router with consistent route prefix and tags
router = APIRouter(prefix="/api/training_catalog", tags=["training_catalog"])


@router.get(
    "",
    summary="Retrieve training catalog",
    response_description="List of all trainable units",
)
def get_catalog(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    """
    Return the full training catalog of unit types, including their tier,
    training time, resource costs, and prerequisite requirements.
    """
    rows = list_units(db)
    return {"catalog": rows}
