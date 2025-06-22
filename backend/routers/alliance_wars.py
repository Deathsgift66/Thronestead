# Project Name: Thronestead©
# File Name: alliance_wars.py
# Version: 6.20.2025.21.10
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from services.audit_service import log_action

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

@router.post("/declare", response_model=None)
def declare_war(payload: DeclarePayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    row = db.execute(
        text(
            "INSERT INTO alliance_wars (attacker_alliance_id, defender_alliance_id, phase, war_status) "
            "VALUES (:att, :def, 'alert', 'pending') RETURNING alliance_war_id"
        ),
        {"att": payload.attacker_alliance_id, "def": payload.defender_alliance_id},
    ).fetchone()
    db.commit()
    log_action(db, user_id, "Declare War", f"{payload.attacker_alliance_id} → {payload.defender_alliance_id}")
    return {"status": "pending", "alliance_war_id": row[0]}


@router.post("/respond", response_model=None)
def respond_war(payload: RespondPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
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
    log_action(db, user_id, f"War {status.title()}", f"War ID {payload.alliance_war_id}")
    return {"status": status}


@router.post("/surrender", response_model=None)
def surrender_war(payload: SurrenderPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    victor = "defender" if payload.side == "attacker" else "attacker"
    db.execute(
        text(
            "UPDATE alliance_wars SET war_status = 'surrendered', phase = 'ended', end_date = now() "
            "WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id},
    )
    db.commit()
    log_action(db, user_id, "Surrender", f"War ID {payload.alliance_war_id}, {payload.side} surrendered")
    return {"status": "surrendered", "victor": victor}


# ----------- Viewing & Tracking -----------

@router.get("/list", response_model=None)
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


@router.get("/view", response_model=None)
def view_war_details(alliance_war_id: int, db: Session = Depends(get_db)):
    war = db.execute(
        text("SELECT * FROM alliance_wars WHERE alliance_war_id = :wid"),
        {"wid": alliance_war_id},
    ).mappings().first()
    if not war:
        raise HTTPException(status_code=404, detail="War not found")
    return {"war": war}


@router.get("/active", response_model=None)
def list_active_wars(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM alliance_wars WHERE war_status = 'active'"))
    return {"wars": [dict(r._mapping) for r in rows]}


# ----------- Additional Data Endpoints -----------

class JoinPayload(BaseModel):
    alliance_war_id: int
    side: str  # "attacker" or "defender"


@router.get("/combat-log", response_model=None)
def get_combat_log(alliance_war_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            "SELECT * FROM alliance_war_combat_logs WHERE alliance_war_id = :wid ORDER BY tick_number"
        ),
        {"wid": alliance_war_id},
    ).mappings().fetchall()
    return {"combat_logs": [dict(r) for r in rows]}


@router.get("/scoreboard", response_model=None)
def get_scoreboard(alliance_war_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM alliance_war_scores WHERE alliance_war_id = :wid"),
        {"wid": alliance_war_id},
    ).mappings().first()
    return row or {}


@router.post("/join", response_model=None)
def join_war(payload: JoinPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    from .progression_router import get_kingdom_id

    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            """
            INSERT INTO alliance_war_participants (alliance_war_id, kingdom_id, role)
            VALUES (:wid, :kid, :side)
            ON CONFLICT (alliance_war_id, kingdom_id) DO UPDATE SET role = EXCLUDED.role
            """
        ),
        {"wid": payload.alliance_war_id, "kid": kid, "side": payload.side},
    )
    db.commit()
    log_action(db, user_id, "Join War", f"War {payload.alliance_war_id} as {payload.side}")
    return {"status": "joined"}


# ----------- Pre-Plan Editing -----------

class PreplanPayload(BaseModel):
    alliance_war_id: int
    preplan_jsonb: dict


@router.get("/preplan", response_model=None)
def get_preplan(alliance_war_id: int, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    from .progression_router import get_kingdom_id

    kid = get_kingdom_id(db, user_id)
    row = db.execute(
        text(
            "SELECT preplan_jsonb FROM alliance_war_preplans "
            "WHERE alliance_war_id = :wid AND kingdom_id = :kid"
        ),
        {"wid": alliance_war_id, "kid": kid},
    ).mappings().first()

    return {"plan": row["preplan_jsonb"] if row else {}}


@router.post("/preplan/submit", response_model=None)
def submit_preplan(payload: PreplanPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    from .progression_router import get_kingdom_id

    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            """
            INSERT INTO alliance_war_preplans (alliance_war_id, kingdom_id, preplan_jsonb)
            VALUES (:wid, :kid, :plan)
            ON CONFLICT (alliance_war_id, kingdom_id)
              DO UPDATE SET preplan_jsonb = EXCLUDED.preplan_jsonb, last_updated = now()
            """
        ),
        {"wid": payload.alliance_war_id, "kid": kid, "plan": payload.preplan_jsonb},
    )
    db.commit()
    log_action(db, user_id, "Save Preplan", str(payload.alliance_war_id))
    return {"status": "saved"}
