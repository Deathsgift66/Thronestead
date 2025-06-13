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


def get_alliance_id(db: Session, user_id: str) -> int:
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]


class ProposePayload(BaseModel):
    treaty_type: str
    partner_alliance_id: int
    notes: str | None = None
    end_date: str | None = None


class RespondPayload(BaseModel):
    treaty_id: int
    response_action: str


@router.get("/summary")
def summary(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    aid = get_alliance_id(db, user_id)

    score_row = db.execute(
        text("SELECT diplomacy_score FROM alliances WHERE alliance_id = :aid"),
        {"aid": aid},
    ).fetchone()
    diplomacy_score = score_row[0] if score_row else 0

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

    partner_rows = db.execute(
        text(
            "SELECT treaty_type, partner_alliance_id FROM alliance_treaties "
            "WHERE (alliance_id = :aid OR partner_alliance_id = :aid) AND status = 'active'"
        ),
        {"aid": aid},
    ).fetchall()
    partners: dict[str, list[int]] = {}
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
    aid = get_alliance_id(db, user_id)
    db.execute(
        text(
            "UPDATE alliance_treaties SET status = 'expired'"
            " WHERE status = 'active' AND end_date IS NOT NULL AND end_date < now()"
        )
    )
    db.commit()
    rows = db.execute(
        text(
            """
            SELECT t.treaty_id,
                   t.treaty_type,
                   CASE WHEN t.alliance_id = :aid THEN t.partner_alliance_id ELSE t.alliance_id END AS partner_id,
                   t.status,
                   t.signed_at,
                   t.end_date,
                   t.notes,
                   a.name AS partner_name,
                   a.emblem_url
              FROM alliance_treaties t
              JOIN alliances a ON a.alliance_id = CASE WHEN t.alliance_id = :aid THEN t.partner_alliance_id ELSE t.alliance_id END
             WHERE (t.alliance_id = :aid OR t.partner_alliance_id = :aid)
             {status}
             ORDER BY t.signed_at DESC
            """
        ).format(status="" if not status_filter else "AND t.status = :st"),
        {"aid": aid, "st": status_filter} if status_filter else {"aid": aid},
    ).fetchall()
    return [
        {
            "treaty_id": r[0],
            "treaty_type": r[1],
            "partner_alliance_id": r[2],
            "status": r[3],
            "signed_at": r[4].isoformat() if r[4] else None,
            "end_date": r[5].isoformat() if r[5] else None,
            "notes": r[6],
            "partner_name": r[7],
            "emblem_url": r[8],
        }
        for r in rows
    ]


@router.post("/propose_treaty")
def propose_treaty(
    payload: ProposePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    aid = get_alliance_id(db, user_id)
    db.execute(
        text(
            "INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status, notes, end_date) "
            "VALUES (:aid, :type, :pid, 'proposed', :notes, :end_date)"
        ),
        {
            "aid": aid,
            "type": payload.treaty_type,
            "pid": payload.partner_alliance_id,
            "notes": payload.notes,
            "end_date": payload.end_date,
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
    treaty = db.execute(
        text(
            "SELECT alliance_id, partner_alliance_id FROM alliance_treaties WHERE treaty_id = :tid"
        ),
        {"tid": payload.treaty_id},
    ).fetchone()
    if not treaty:
        raise HTTPException(status_code=404, detail="Treaty not found")
    aid = get_alliance_id(db, user_id)
    if aid not in treaty:
        raise HTTPException(status_code=403, detail="Not authorized")

    if payload.response_action == "accept":
        status = "active"
    elif payload.response_action in ("reject", "cancel"):
        status = "cancelled"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    db.execute(
        text(
            "UPDATE alliance_treaties SET status = :st, signed_at = now() WHERE treaty_id = :tid"
        ),
        {"st": status, "tid": payload.treaty_id},
    )
    db.commit()
    log_alliance_activity(db, aid, f"Treaty {status.capitalize()}", str(payload.treaty_id))
    return {"status": status}


@router.post("/renew_treaty")
def renew_treaty(
    treaty_id: int,
    end_date: str | None = None,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            "SELECT alliance_id, partner_alliance_id, treaty_type FROM alliance_treaties WHERE treaty_id = :tid"
        ),
        {"tid": treaty_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Treaty not found")
    aid = get_alliance_id(db, user_id)
    if aid not in row[:2]:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.execute(text("UPDATE alliance_treaties SET status = 'expired' WHERE treaty_id = :tid"), {"tid": treaty_id})
    db.execute(
        text(
            "INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status, end_date) "
            "VALUES (:aid, :type, :pid, 'active', :ed)"
        ),
        {"aid": row[0], "type": row[2], "pid": row[1], "ed": end_date},
    )
    db.commit()
    log_alliance_activity(db, aid, "Treaty Renewed", str(treaty_id))
    return {"status": "renewed"}


@router.get("/war_status")
def war_status(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    aid = get_alliance_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT w.attacker_alliance_id,
                   w.defender_alliance_id,
                   w.war_status,
                   w.start_date,
                   w.end_date,
                   s.victor
              FROM alliance_wars w
              LEFT JOIN alliance_war_scores s ON w.alliance_war_id = s.alliance_war_id
             WHERE w.attacker_alliance_id = :aid OR w.defender_alliance_id = :aid
             ORDER BY w.start_date DESC
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
            "victor": r[5],
        }
        for r in rows
    ]
