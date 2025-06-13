# Project Name: Kingmakers Rise©
# File Name: training_catalog.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.training_catalog_service import list_units

router = APIRouter(prefix="/api/training_catalog", tags=["training_catalog"])


@router.get("")
def get_catalog(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return the full training catalog."""
    rows = list_units(db)
    return {"catalog": rows}
