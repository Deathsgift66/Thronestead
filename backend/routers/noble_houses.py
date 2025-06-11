from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import NobleHouse

router = APIRouter(prefix="/api/noble_houses", tags=["noble_houses"])


class HousePayload(BaseModel):
    name: str
    motto: str | None = None
    crest: str | None = None
    region: str | None = None
    description: str | None = None


def _serialize(row: NobleHouse) -> dict:
    return {
        "house_id": row.house_id,
        "name": row.name,
        "motto": row.motto,
        "crest": row.crest,
        "region": row.region,
        "description": row.description,
    }


@router.get("")
def list_houses(db: Session = Depends(get_db)):
    rows = db.query(NobleHouse).all()
    return {"houses": [_serialize(r) for r in rows]}


@router.get("/{house_id}")
def get_house(house_id: int, db: Session = Depends(get_db)):
    row = db.query(NobleHouse).filter_by(house_id=house_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="House not found")
    return _serialize(row)


@router.post("")
def create_house(payload: HousePayload, db: Session = Depends(get_db)):
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
    return {"house_id": house.house_id}


@router.put("/{house_id}")
def update_house(house_id: int, payload: HousePayload, db: Session = Depends(get_db)):
    house = db.query(NobleHouse).filter_by(house_id=house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    house.name = payload.name
    house.motto = payload.motto
    house.crest = payload.crest
    house.region = payload.region
    house.description = payload.description
    db.commit()
    return {"message": "updated"}


@router.delete("/{house_id}")
def delete_house(house_id: int, db: Session = Depends(get_db)):
    house = db.query(NobleHouse).filter_by(house_id=house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    db.delete(house)
    db.commit()
    return {"message": "deleted"}
