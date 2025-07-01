# Project Name: Thronestead©
# File Name: alliance_wars.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_wars.py
Role: API routes for alliance wars.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id, require_active_user_id
from ..enums import WarPhase

router = APIRouter(prefix="/api/alliance-wars", tags=["alliance_wars"])


# --- Utility Functions ---


def validate_alliance_permission(db: Session, user_id: str, permission: str) -> int:
    """Return the user's alliance_id if they have ``permission`` or raise 403."""
    row = db.execute(
        text(
            """
            SELECT m.alliance_id, r.permissions
              FROM alliance_members m
              JOIN alliance_roles r ON m.role_id = r.role_id
             WHERE m.user_id = :uid
            """
        ),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Not authorized")
    alliance_id, perms = row
    if not perms or permission not in perms:
        raise HTTPException(status_code=403, detail="Permission required")
    return alliance_id


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
def declare_war(
    payload: DeclarePayload,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    aid = validate_alliance_permission(db, user_id, "can_manage_wars")
    if aid != payload.attacker_alliance_id:
        raise HTTPException(status_code=403, detail="Cannot declare for this alliance")

    row = db.execute(
        text(
            "INSERT INTO alliance_wars (attacker_alliance_id, defender_alliance_id, phase, war_status) "
            "VALUES (:att, :def, :phase, 'pending') RETURNING alliance_war_id"
        ),
        {
            "att": payload.attacker_alliance_id,
            "def": payload.defender_alliance_id,
            "phase": WarPhase.ALERT.value,
        },
    ).fetchone()
    db.commit()
    log_action(
        db,
        user_id,
        "Declare War",
        f"{payload.attacker_alliance_id} → {payload.defender_alliance_id}",
    )
    return {"status": "pending", "alliance_war_id": row[0]}


@router.post("/respond")
def respond_war(
    payload: RespondPayload,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    status = "active" if payload.action == "accept" else "cancelled"
    war_row = db.execute(
        text(
            "SELECT attacker_alliance_id, defender_alliance_id FROM alliance_wars WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id},
    ).fetchone()
    if not war_row:
        raise HTTPException(status_code=404, detail="War not found")

    aid = validate_alliance_permission(db, user_id, "can_manage_wars")
    if aid not in war_row:
        raise HTTPException(status_code=403, detail="Not part of this war")

    db.execute(
        text(
            """
            UPDATE alliance_wars
               SET war_status = :status,
                   phase = CASE WHEN :status = 'active' THEN :live_phase ELSE phase END,
                   start_date = CASE WHEN :status = 'active' THEN now() ELSE start_date END
             WHERE alliance_war_id = :wid
        """
        ),
        {"status": status, "wid": payload.alliance_war_id, "live_phase": WarPhase.LIVE.value},
    )
    db.commit()
    log_action(
        db, user_id, f"War {status.title()}", f"War ID {payload.alliance_war_id}"
    )
    return {"status": status}


@router.post("/surrender")
def surrender_war(
    payload: SurrenderPayload,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    victor = "defender" if payload.side == "attacker" else "attacker"
    war_row = db.execute(
        text(
            "SELECT attacker_alliance_id, defender_alliance_id FROM alliance_wars WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id},
    ).fetchone()
    if not war_row:
        raise HTTPException(status_code=404, detail="War not found")

    aid = validate_alliance_permission(db, user_id, "can_manage_wars")
    if payload.side == "attacker" and aid != war_row[0]:
        raise HTTPException(status_code=403, detail="Cannot surrender for this side")
    if payload.side == "defender" and aid != war_row[1]:
        raise HTTPException(status_code=403, detail="Cannot surrender for this side")

    db.execute(
        text(
            "UPDATE alliance_wars SET war_status = 'surrendered', phase = :phase, end_date = now() "
            "WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id, "phase": WarPhase.RESOLVED.value},
    )
    db.commit()
    log_action(
        db,
        user_id,
        "Surrender",
        f"War ID {payload.alliance_war_id}, {payload.side} surrendered",
    )
    return {"status": "surrendered", "victor": victor}


# ----------- Viewing & Tracking -----------


@router.get("/list")
def list_wars(alliance_id: int, db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text(
                """
        SELECT * FROM alliance_wars
        WHERE attacker_alliance_id = :aid OR defender_alliance_id = :aid
        ORDER BY start_date DESC
    """
            ),
            {"aid": alliance_id},
        )
        .mappings()
        .fetchall()
    )

    wars = [dict(r) for r in rows]
    return {
        "active_wars": [w for w in wars if w["war_status"] == "active"],
        "completed_wars": [w for w in wars if w["war_status"] == "completed"],
        "upcoming_wars": [
            w for w in wars if w["war_status"] not in ("active", "completed")
        ],
    }


@router.get("/view")
def view_war_details(alliance_war_id: int, db: Session = Depends(get_db)):
    war = (
        db.execute(
            text("SELECT * FROM alliance_wars WHERE alliance_war_id = :wid"),
            {"wid": alliance_war_id},
        )
        .mappings()
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="War not found")
    return {"war": war}


@router.get("/active")
def list_active_wars(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM alliance_wars WHERE war_status = 'active'"))
    return {"wars": [dict(r._mapping) for r in rows]}


# ----------- Additional Data Endpoints -----------


class JoinPayload(BaseModel):
    alliance_war_id: int
    side: str  # "attacker" or "defender"


@router.get("/combat-log")
def get_combat_log(alliance_war_id: int, db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text(
                "SELECT * FROM alliance_war_combat_logs WHERE alliance_war_id = :wid ORDER BY tick_number"
            ),
            {"wid": alliance_war_id},
        )
        .mappings()
        .fetchall()
    )
    return {"combat_logs": [dict(r) for r in rows]}


@router.get("/scoreboard")
def get_scoreboard(alliance_war_id: int, db: Session = Depends(get_db)):
    row = (
        db.execute(
            text("SELECT * FROM alliance_war_scores WHERE alliance_war_id = :wid"),
            {"wid": alliance_war_id},
        )
        .mappings()
        .first()
    )
    return row or {}


@router.post("/join")
def join_war(
    payload: JoinPayload,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    from .progression_router import get_kingdom_id
    kid = get_kingdom_id(db, user_id)

    war_row = db.execute(
        text(
            "SELECT attacker_alliance_id, defender_alliance_id FROM alliance_wars WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id},
    ).fetchone()
    if not war_row:
        raise HTTPException(status_code=404, detail="War not found")

    aid = validate_alliance_permission(db, user_id, "can_join_wars")
    target = war_row[0] if payload.side == "attacker" else war_row[1]
    if aid != target:
        raise HTTPException(status_code=403, detail="Cannot join for this side")

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

    morale_row = db.execute(
        text(
            """
            SELECT morale, morale_bonus_buildings, morale_bonus_tech, morale_bonus_events
              FROM kingdom_troop_slots WHERE kingdom_id = :kid
            """
        ),
        {"kid": kid},
    ).fetchone()

    base = morale_row[0] if morale_row else 0
    bld = morale_row[1] if morale_row else 0
    tech = morale_row[2] if morale_row else 0
    events = morale_row[3] if morale_row else 0
    morale = (base or 0) + (bld or 0) + (tech or 0) + (events or 0)
    if morale <= 1:
        morale *= 100
    morale = min(100, morale)

    db.execute(
        text(
            """
            INSERT INTO unit_movements (
                war_id, kingdom_id, unit_type, quantity,
                position_x, position_y, stance, morale
            ) VALUES (:wid, :kid, 'infantry', 10, 0, 0, 'hold_ground', :morale)
            """
        ),
        {"wid": payload.alliance_war_id, "kid": kid, "morale": morale},
    )
    db.commit()
    log_action(
        db, user_id, "Join War", f"War {payload.alliance_war_id} as {payload.side}"
    )
    return {"status": "joined"}


# ----------- Pre-Plan Editing -----------


class PreplanPayload(BaseModel):
    alliance_war_id: int
    preplan_jsonb: dict


@router.get("/preplan")
def get_preplan(
    alliance_war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    from .progression_router import get_kingdom_id

    kid = get_kingdom_id(db, user_id)
    row = (
        db.execute(
            text(
                "SELECT preplan_jsonb FROM alliance_war_preplans "
                "WHERE alliance_war_id = :wid AND kingdom_id = :kid"
            ),
            {"wid": alliance_war_id, "kid": kid},
        )
        .mappings()
        .first()
    )

    return {"plan": row["preplan_jsonb"] if row else {}}


@router.post("/preplan/submit")
def submit_preplan(
    payload: PreplanPayload,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
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
