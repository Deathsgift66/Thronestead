from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/api/alliance-treaties", tags=["alliance_treaties"])


class TreatyCreate(BaseModel):
    alliance_id: int = 1
    partner_alliance_id: int
    treaty_type: str


class TreatyAction(BaseModel):
    treaty_id: int


@router.get("")
def list_treaties(alliance_id: int = 1, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at
            FROM alliance_treaties
            WHERE alliance_id = :aid OR partner_alliance_id = :aid
            ORDER BY signed_at DESC
            """
        ),
        {"aid": alliance_id},
    ).fetchall()
    treaties = [
        {
            "treaty_id": r[0],
            "alliance_id": r[1],
            "treaty_type": r[2],
            "partner_alliance_id": r[3],
            "status": r[4],
            "signed_at": r[5].isoformat() if r[5] else None,
        }
        for r in rows
    ]
    return {"treaties": treaties}


@router.post("/create")
def create_treaty(payload: TreatyCreate, db: Session = Depends(get_db)):
    db.execute(
        text(
            """
            INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status, signed_at)
            VALUES (:aid, :type, :pid, 'proposed', now())
            """
        ),
        {"aid": payload.alliance_id, "type": payload.treaty_type, "pid": payload.partner_alliance_id},
    )
    db.commit()
    return {"message": "Treaty proposed"}


@router.post("/accept")
def accept_treaty(payload: TreatyAction, db: Session = Depends(get_db)):
    db.execute(
        text(
            "UPDATE alliance_treaties SET status = 'active', signed_at = now() WHERE treaty_id = :tid"
        ),
        {"tid": payload.treaty_id},
    )
    db.commit()
    return {"message": "Treaty accepted"}


@router.post("/cancel")
def cancel_treaty(payload: TreatyAction, db: Session = Depends(get_db)):
    db.execute(
        text("UPDATE alliance_treaties SET status = 'cancelled' WHERE treaty_id = :tid"),
        {"tid": payload.treaty_id},
    )
    db.commit()
    return {"message": "Treaty cancelled"}


