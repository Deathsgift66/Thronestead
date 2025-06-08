from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/api/buildings", tags=["buildings"])


class UpgradePayload(BaseModel):
    building: str


@router.post("/upgrade")
async def upgrade(payload: UpgradePayload):
    return {"message": "upgrading", "building": payload.building}


@router.get("/catalogue")
def get_catalogue(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM building_catalogue ORDER BY building_id")).mappings().fetchall()
    return {"buildings": [dict(r) for r in rows]}

