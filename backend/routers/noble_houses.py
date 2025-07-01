# Project Name: Thronestead©
# File Name: noble_houses.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: noble_houses.py
Role: API routes for noble houses.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import NobleHouse

router = APIRouter(prefix="/api/noble_houses", tags=["noble_houses"])


# ---------- Data Models ----------


class HousePayload(BaseModel):
    """Request payload for creating or updating noble houses."""

    name: str
    motto: str | None = None
    crest: str | None = None
    region: str | None = None
    description: str | None = None


# ---------- Internal Utilities ----------


def _serialize(row: NobleHouse) -> dict:
    """Convert a NobleHouse ORM object into a dictionary."""
    return {
        "house_id": row.house_id,
        "name": row.name,
        "motto": row.motto,
        "crest": row.crest,
        "region": row.region,
        "description": row.description,
    }


# ---------- Route Endpoints ----------


@router.get("")
def list_houses(db: Session = Depends(get_db)):
    """Return a list of all noble houses."""
    rows = db.query(NobleHouse).all()
    return {"houses": [_serialize(r) for r in rows]}


@router.get("/{house_id}")
def get_house(house_id: int, db: Session = Depends(get_db)):
    """Return data for a specific noble house."""
    row = db.query(NobleHouse).filter_by(house_id=house_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="House not found")
    return _serialize(row)


@router.post("")
def create_house(payload: HousePayload, db: Session = Depends(get_db)):
    """Create a new noble house entry."""
    house = NobleHouse(
        name=payload.name,
        motto=payload.motto,
        crest=payload.crest,
        region=payload.region,
        description=payload.description,
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    return {"house_id": house.house_id, "message": "House created successfully"}


@router.put("/{house_id}")
def update_house(house_id: int, payload: HousePayload, db: Session = Depends(get_db)):
    """Update an existing noble house entry."""
    house = db.query(NobleHouse).filter_by(house_id=house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    # Update all editable fields
    house.name = payload.name
    house.motto = payload.motto
    house.crest = payload.crest
    house.region = payload.region
    house.description = payload.description

    db.commit()
    return {"message": "House updated successfully"}


@router.delete("/{house_id}")
def delete_house(house_id: int, db: Session = Depends(get_db)):
    """Delete an existing noble house."""
    house = db.query(NobleHouse).filter_by(house_id=house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    db.delete(house)
    db.commit()
    return {"message": "House deleted successfully"}
