# Project Name: Kingmakers Rise©
# File Name: diplomacy_center.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.audit_service import log_alliance_activity

router = APIRouter(prefix="/api/diplomacy", tags=["diplomacy_center"])

# --------------------
# Utility
# --------------------
def get_alliance_id(db: Session, user_id: str) -> int:
    """Retrieve the alliance_id of a given user."""
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]


# --------------------
# Pydantic Payloads
# --------------------
class ProposePayload(BaseModel):
    treaty_type: str
    partner_alliance_id: int


class RespondPayload(BaseModel):
    treaty_id: int
    response_action: str


# --------------------
# Routes
# --------------------
@router.get("/summary")
def summary(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return diplomacy summary including treaties and war stats."""
    aid = get_alliance_id(db, user_id)

    diplomacy_score = db.execute(
        text("SELECT diplomacy_score FROM alliances WHERE alliance_id = :aid"),
        {"aid": aid},
    ).scalar() or 0

    treaty_count = db.execute(
        text(
            "SELECT COUNT(*) FROM alliance_treaties "
            "WHERE (alliance_id = :aid OR partner_alliance_id = :aid) "
            "AND status IN ('active','proposed')"
        ),
        {"aid": aid},
    ).scalar() or 0

    war_rows = db.execute(
        text(
            "SELECT war_status FROM alliance_wars "
            "WHERE attacker_alliance_id = :aid OR defender_alliance_id = :aid"
        ),
        {"aid": aid},
    ).fetchall()
    total_wars = len(war_rows)
    ongoing_wars = sum(1 for r in war_rows if r[0] == "active")

    partners = {}
    partner_rows = db.execute(
        text(
            "SELECT treaty_type, partner_alliance_id FROM alliance_treaties "
            "WHERE (alliance_id = :aid OR partner_alliance_id = :aid) AND status = 'active'"
        ),
        {"aid": aid},
    ).fetchall()
    for ttype, pid in partner_rows:
        partners.setdefault(ttype, []).append(pid)

    return {
        "diplomacy_score": diplomacy_score,
        "active_treaties": treaty_count,
        "ongoing_wars": ongoing_wars,
        "total_wars": total_wars,
        "treaty_partners": partners,
    }


@router.get("/treaties")
def list_treaties(
    status_filter: str | None = Query(None, alias="filter"),
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """List treaties for the user's alliance, optionally filtered by status."""
    aid = get_alliance_id(db, user_id)

    # Auto-expire old treaties older than 30 days
    db.execute(
        text(
            "UPDATE alliance_treaties SET status = 'expired' "
            "WHERE status = 'active' AND signed_at < now() - interval '30 days'"
        )
    )
    db.commit()

    rows = db.execute(
        text(
            f"""
            SELECT t.treaty_id, t.treaty_type,
                   CASE WHEN t.alliance_id = :aid THEN t.partner_alliance_id ELSE t.alliance_id END AS partner_id,
                   t.status, t.signed_at,
                   a.name AS partner_name, a.emblem_url
            FROM alliance_treaties t
            JOIN alliances a ON a.alliance_id = CASE WHEN t.alliance_id = :aid THEN t.partner_alliance_id ELSE t.alliance_id END
            WHERE (t.alliance_id = :aid OR t.partner_alliance_id = :aid)
            {"AND t.status = :st" if status_filter else ""}
            ORDER BY t.signed_at DESC
            """
        ),
        {"aid": aid, "st": status_filter} if status_filter else {"aid": aid},
    ).fetchall()

    return [
        {
            "treaty_id": r[0],
            "treaty_type": r[1],
            "partner_alliance_id": r[2],
            "status": r[3],
            "signed_at": r[4].isoformat() if r[4] else None,
            "partner_name": r[5],
            "emblem_url": r[6],
        }
        for r in rows
    ]


@router.post("/propose_treaty")
def propose_treaty(
    payload: ProposePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Propose a new treaty to another alliance."""
    aid = get_alliance_id(db, user_id)
    db.execute(
        text(
            "INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status) "
            "VALUES (:aid, :type, :pid, 'proposed')"
        ),
        {
            "aid": aid,
            "type": payload.treaty_type,
            "pid": payload.partner_alliance_id,
        },
    )
    db.commit()
    log_alliance_activity(db, aid, user_id, "Treaty Proposed", payload.treaty_type)
    return {"status": "proposed"}


@router.post("/respond_treaty")
def respond_treaty(
    payload: RespondPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Accept, reject or cancel a treaty."""
    treaty = db.execute(
        text("SELECT alliance_id, partner_alliance_id FROM alliance_treaties WHERE treaty_id = :tid"),
        {"tid": payload.treaty_id},
    ).fetchone()
    if not treaty:
        raise HTTPException(status_code=404, detail="Treaty not found")

    aid = get_alliance_id(db, user_id)
    if aid not in treaty:
        raise HTTPException(status_code=403, detail="Not authorized")

    action_map = {
        "accept": "active",
        "reject": "cancelled",
        "cancel": "cancelled"
    }
    if payload.response_action not in action_map:
        raise HTTPException(status_code=400, detail="Invalid action")

    new_status = action_map[payload.response_action]

    db.execute(
        text("UPDATE alliance_treaties SET status = :st, signed_at = now() WHERE treaty_id = :tid"),
        {"st": new_status, "tid": payload.treaty_id},
    )
    db.commit()
    log_alliance_activity(db, aid, f"Treaty {new_status.capitalize()}", str(payload.treaty_id))
    return {"status": new_status}


@router.post("/renew_treaty")
def renew_treaty(
    treaty_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Renew an expired treaty."""
    row = db.execute(
        text("SELECT alliance_id, partner_alliance_id, treaty_type FROM alliance_treaties WHERE treaty_id = :tid"),
        {"tid": treaty_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Treaty not found")

    aid = get_alliance_id(db, user_id)
    if aid not in row[:2]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Mark old one expired
    db.execute(
        text("UPDATE alliance_treaties SET status = 'expired' WHERE treaty_id = :tid"),
        {"tid": treaty_id},
    )

    # Insert new
    db.execute(
        text(
            "INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status) "
            "VALUES (:aid, :type, :pid, 'active')"
        ),
        {"aid": row[0], "type": row[2], "pid": row[1]},
    )
    db.commit()
    log_alliance_activity(db, aid, "Treaty Renewed", str(treaty_id))
    return {"status": "renewed"}


@router.get("/war_status")
def war_status(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """List war status entries related to your alliance."""
    aid = get_alliance_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT attacker_alliance_id,
                   defender_alliance_id,
                   war_status,
                   start_date,
                   end_date
              FROM alliance_wars
             WHERE attacker_alliance_id = :aid OR defender_alliance_id = :aid
             ORDER BY start_date DESC
            """
        ),
        {"aid": aid},
    ).fetchall()

    return [
        {
            "attacker_alliance_id": r[0],
            "defender_alliance_id": r[1],
            "war_status": r[2],
            "start_date": r[3].isoformat() if r[3] else None,
            "end_date": r[4].isoformat() if r[4] else None,
        }
        for r in rows
    ]
