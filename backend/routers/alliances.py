from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alliance, AllianceVault

router = APIRouter(prefix="/api/alliances", tags=["alliances"])


class AllianceCreate(BaseModel):
    name: str
    leader: str | None = None


@router.post("/create")
def create_alliance(payload: AllianceCreate, db: Session = Depends(get_db)):
    alliance = Alliance(name=payload.name, leader=payload.leader)
    db.add(alliance)
    db.flush()  # Populate alliance_id

    vault = AllianceVault(alliance_id=alliance.alliance_id)
    db.add(vault)
    db.commit()

    return {"alliance_id": alliance.alliance_id}
