from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id
from services.audit_service import log_action, log_alliance_activity
from backend.models import Notification

router = APIRouter(prefix="/api/alliance-wars", tags=["alliance_wars"])


def get_alliance_id(db: Session, user_id: str) -> int:
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]


def authorize_war_access(db: Session, user_id: str, war_id: int) -> None:
    """Ensure the requesting user belongs to one of the alliances in the war."""
    aid = get_alliance_id(db, user_id)
    row = db.execute(
        text(
            "SELECT attacker_alliance_id, defender_alliance_id "
            "FROM alliance_wars WHERE alliance_war_id = :wid"
        ),
        {"wid": war_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="War not found")
    if aid not in row:
        raise HTTPException(status_code=403, detail="Access denied")


class DeclarePayload(BaseModel):
    defender_alliance_id: int


class RespondPayload(BaseModel):
    alliance_war_id: int
    action: str


@router.post("/declare")
def declare_war(
    payload: DeclarePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    attacker = get_alliance_id(db, user_id)
    row = db.execute(
        text(
            "INSERT INTO alliance_wars (attacker_alliance_id, defender_alliance_id, phase, war_status) "
            "VALUES (:att, :def, 'alert', 'pending') RETURNING alliance_war_id"
        ),
        {"att": attacker, "def": payload.defender_alliance_id},
    ).fetchone()
    db.commit()
    war_id = row[0]
    log_alliance_activity(db, attacker, user_id, "Alliance War Declared", str(war_id))
    defenders = db.execute(
        text("SELECT user_id FROM alliance_members WHERE alliance_id = :aid"),
        {"aid": payload.defender_alliance_id},
    ).fetchall()
    for (uid,) in defenders:
        db.add(
            Notification(
                user_id=uid,
                title="Alliance Under Attack",
                message="Your alliance has been attacked!",
                category="war",
                source_system="war",
            )
        )
    db.commit()
    return {"status": "pending", "alliance_war_id": war_id}


@router.post("/respond")
def respond_war(
    payload: RespondPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = get_alliance_id(db, user_id)
    row = db.execute(
        text(
            "SELECT attacker_alliance_id, defender_alliance_id FROM alliance_wars WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="War not found")
    if aid not in row:
        raise HTTPException(status_code=403, detail="Access denied")
    if payload.action == "accept":
        status = "active"
        db.execute(
            text(
                "UPDATE alliance_wars SET war_status = :st, phase = 'battle', start_date = now() WHERE alliance_war_id = :wid"
            ),
            {"st": status, "wid": payload.alliance_war_id},
        )
    else:
        status = "cancelled"
        db.execute(
            text("UPDATE alliance_wars SET war_status = :st WHERE alliance_war_id = :wid"),
            {"st": status, "wid": payload.alliance_war_id},
        )
    db.commit()
    return {"status": status}


@router.get("/list")
def list_wars(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = get_alliance_id(db, user_id)
    rows = (
        db.execute(
            text(
                "SELECT * FROM alliance_wars "
                "WHERE attacker_alliance_id = :aid OR defender_alliance_id = :aid "
                "ORDER BY start_date DESC"
            ),
            {"aid": aid},
        )
        .mappings()
        .fetchall()
    )
    wars = [dict(r) for r in rows]
    active = [w for w in wars if w.get("war_status") == "active"]
    completed = [w for w in wars if w.get("war_status") == "completed"]
    upcoming = [w for w in wars if w.get("war_status") not in ("active", "completed")]
    return {
        "active_wars": active,
        "completed_wars": completed,
        "upcoming_wars": upcoming,
    }


@router.get("/view")
def view_war_details(
    alliance_war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, alliance_war_id)
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
    terrain = (
        db.execute(
            text("SELECT * FROM terrain_map WHERE war_id = :wid"),
            {"wid": alliance_war_id},
        )
        .mappings()
        .first()
    )
    score = (
        db.execute(
            text("SELECT * FROM alliance_war_scores WHERE alliance_war_id = :wid"),
            {"wid": alliance_war_id},
        )
        .mappings()
        .first()
    )
    return {"war": war, "map": terrain, "score": score}


@router.get("/combat-log")
def get_combat_logs(
    alliance_war_id: int,
    since_tick: int = 0,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, alliance_war_id)
    rows = (
        db.execute(
            text(
                "SELECT * FROM alliance_war_combat_logs "
                "WHERE alliance_war_id = :wid AND tick_number >= :tick "
                "ORDER BY tick_number"
            ),
            {"wid": alliance_war_id, "tick": since_tick},
        )
        .mappings()
        .fetchall()
    )
    return [dict(r) for r in rows]


@router.get("/preplan")
def get_preplan(
    alliance_war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, alliance_war_id)
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
    alliance_war_id: int,
    preplan_jsonb: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, alliance_war_id)
    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            "INSERT INTO alliance_war_preplans (alliance_war_id, kingdom_id, preplan_jsonb, last_updated) "
            "VALUES (:wid, :kid, :plan, now()) "
            "ON CONFLICT (alliance_war_id, kingdom_id) DO UPDATE SET preplan_jsonb = :plan, last_updated = now()"
        ),
        {"wid": alliance_war_id, "kid": kid, "plan": preplan_jsonb},
    )
    log_action(db, user_id, "Preplan Submitted", f"Alliance War ID {alliance_war_id}")
    db.commit()
    return {"status": "submitted"}


@router.get("/scoreboard")
def get_scoreboard(
    alliance_war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, alliance_war_id)
    row = (
        db.execute(
            text("SELECT * FROM alliance_war_scores WHERE alliance_war_id = :wid"),
            {"wid": alliance_war_id},
        )
        .mappings()
        .first()
    )
    return {"score": dict(row) if row else {}}


@router.get("/participants")
def get_participants(
    alliance_war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, alliance_war_id)
    rows = (
        db.execute(
            text(
                "SELECT kingdom_id, role FROM alliance_war_participants WHERE alliance_war_id = :wid"
            ),
            {"wid": alliance_war_id},
        )
        .mappings()
        .fetchall()
    )
    return {"participants": [dict(r) for r in rows]}


@router.get("/active")
def list_active_wars(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text("SELECT * FROM alliance_wars WHERE war_status = 'active'"),
        )
        .mappings()
        .fetchall()
    )
    return {"wars": [dict(r) for r in rows]}


class JoinPayload(BaseModel):
    alliance_war_id: int
    side: str


@router.post("/join")
def request_join(
    payload: JoinPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, payload.alliance_war_id)
    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            "INSERT INTO alliance_war_participants (alliance_war_id, kingdom_id, role) "
            "VALUES (:wid, :kid, :role) ON CONFLICT DO NOTHING"
        ),
        {"wid": payload.alliance_war_id, "kid": kid, "role": payload.side},
    )
    db.execute(
        text(
            "INSERT INTO alliance_war_scores (alliance_war_id, battles_participated) "
            "VALUES (:wid, 1) "
            "ON CONFLICT (alliance_war_id) DO UPDATE SET battles_participated = alliance_war_scores.battles_participated + 1, last_updated = now()"
        ),
        {"wid": payload.alliance_war_id},
    )
    db.commit()
    return {"status": "joined"}


class SurrenderPayload(BaseModel):
    alliance_war_id: int
    side: str


@router.post("/surrender")
def surrender_war(
    payload: SurrenderPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, payload.alliance_war_id)
    victor = "defender" if payload.side == "attacker" else "attacker"
    db.execute(
        text(
            "UPDATE alliance_wars SET war_status = 'surrendered', phase = 'ended', end_date = now() "
            "WHERE alliance_war_id = :wid"
        ),
        {"wid": payload.alliance_war_id},
    )
    db.execute(
        text(
            "INSERT INTO alliance_war_scores (alliance_war_id, victor) VALUES (:wid, :victor) "
            "ON CONFLICT (alliance_war_id) DO UPDATE SET victor = :victor, last_updated = now()"
        ),
        {"wid": payload.alliance_war_id, "victor": victor},
    )
    db.commit()
    return {"status": "surrendered", "victor": victor}


@router.get("/summary")
def war_summary(
    alliance_war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    authorize_war_access(db, user_id, alliance_war_id)
    row = (
        db.execute(
            text("SELECT * FROM alliance_war_scores WHERE alliance_war_id = :wid"),
            {"wid": alliance_war_id},
        )
        .mappings()
        .first()
    )
    return {"summary": dict(row) if row else {}}
