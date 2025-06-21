# Project Name: Thronestead©
# File Name: alliance_wars.py
# Version: 6.13.2025.20.13
# Developer: Deathsgift66

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/api/alliance-wars", tags=["alliance_wars"])

# ----------- Request Payloads -----------

class DeclarePayload(BaseModel):
    attacker_alliance_id: int
    defender_alliance_id: int

class RespondPayload(BaseModel):
    alliance_war_id: int
    action: str  # "accept" or "cancel"

class SurrenderPayload(BaseModel):
    alliance_war_id: int
    side: str  # "attacker" or "defender"

# ----------- War Lifecycle Routes -----------

@router.post("/declare")
def declare_war(payload: DeclarePayload, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            "INSERT INTO alliance_wars (attacker_alliance_id, defender_alliance_id, phase, war_status) "
            "VALUES (:att, :def, 'alert', 'pending') RETURNING alliance_war_id"
        ),
        {"att": payload.attacker_alliance_id, "def": payload.defender_alliance_id},
    ).fetchone()
    db.commit()
    return {"status": "pending", "alliance_war_id": row[0]}


@router.post("/respond")
def respond_war(payload: RespondPayload, db: Session = Depends(get_db)):
    status = "active" if payload.action == "accept" else "cancelled"
    db.execute(
        text("""
            UPDATE alliance_wars 
               SET war_status = :status, 
                   phase = CASE WHEN :status = 'active' THEN 'battle' ELSE phase END, 
                   start_date = CASE WHEN :status = 'active' THEN now() ELSE start_date END 
             WHERE alliance_war_id = :wid
        """),
        {"status": status, "wid": payload.alliance_war_id},
    )
    db.commit()
    return {"status": status}


@router.post("/surrender")
def surrender_war(payload: SurrenderPayload, db: Session = Depends(get_db)):
    victor = "defender" if payload.side == "attacker" else "attacker"
    db.execute(
        text(
            "UPDATE alliance_wars SET war_status = 'surrendered', phase = 'ended', end_date = now() "
            "WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id},
    )
    db.commit()
    return {"status": "surrendered", "victor": victor}


# ----------- Viewing & Tracking -----------

@router.get("/list")
def list_wars(alliance_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT * FROM alliance_wars 
        WHERE attacker_alliance_id = :aid OR defender_alliance_id = :aid
        ORDER BY start_date DESC
    """), {"aid": alliance_id}).mappings().fetchall()

    wars = [dict(r) for r in rows]
    return {
        "active_wars": [w for w in wars if w["war_status"] == "active"],
        "completed_wars": [w for w in wars if w["war_status"] == "completed"],
        "upcoming_wars": [w for w in wars if w["war_status"] not in ("active", "completed")],
    }


@router.get("/view")
def view_war_details(alliance_war_id: int, db: Session = Depends(get_db)):
    war = db.execute(
        text("SELECT * FROM alliance_wars WHERE alliance_war_id = :wid"),
        {"wid": alliance_war_id},
    ).mappings().first()
    return {"war": war}


@router.get("/active")
def list_active_wars(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM alliance_wars WHERE war_status = 'active'"))
    return {"wars": [dict(r) for r in rows.mappings().fetchall()]}
