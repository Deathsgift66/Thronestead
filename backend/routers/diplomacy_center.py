# Project Name: Thronestead©
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


# New API payloads used by metrics/treaty endpoints
class TreatyProposal(BaseModel):
    proposer_id: int
    partner_alliance_id: int
    treaty_type: str
    notes: str | None = None
    end_date: str | None = None


class TreatyResponse(BaseModel):
    treaty_id: int
    response: str


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


# --------------------
# New API Routes
# --------------------

@router.get("/metrics/{alliance_id}")
def metrics(alliance_id: int, db: Session = Depends(get_db)):
    """Return basic diplomacy metrics for an alliance."""
    diplomacy_score = db.execute(
        text("SELECT diplomacy_score FROM alliances WHERE alliance_id = :aid"),
        {"aid": alliance_id},
    ).scalar() or 0

    active_treaties = db.execute(
        text(
            "SELECT COUNT(*) FROM alliance_treaties "
            "WHERE (alliance_id = :aid OR partner_alliance_id = :aid) "
            "AND status = 'active'"
        ),
        {"aid": alliance_id},
    ).scalar() or 0

    ongoing_wars = db.execute(
        text(
            "SELECT COUNT(*) FROM alliance_wars "
            "WHERE (attacker_alliance_id = :aid OR defender_alliance_id = :aid) "
            "AND war_status = 'active'"
        ),
        {"aid": alliance_id},
    ).scalar() or 0

    return {
        "diplomacy_score": diplomacy_score,
        "active_treaties": active_treaties,
        "ongoing_wars": ongoing_wars,
    }


@router.get("/treaties/{alliance_id}")
def treaties(alliance_id: int, status: str | None = Query(None), db: Session = Depends(get_db)):
    """Return treaties for the specified alliance."""
    query = (
        "SELECT t.treaty_id, t.treaty_type, "
        "CASE WHEN t.alliance_id = :aid THEN t.partner_alliance_id ELSE t.alliance_id END AS partner_id, "
        "t.status, t.signed_at, a.name AS partner_name "
        "FROM alliance_treaties t "
        "JOIN alliances a ON a.alliance_id = CASE WHEN t.alliance_id = :aid THEN t.partner_alliance_id ELSE t.alliance_id END "
        "WHERE t.alliance_id = :aid OR t.partner_alliance_id = :aid"
    )
    if status:
        query += " AND status = :st"
    query += " ORDER BY signed_at DESC"
    rows = db.execute(text(query), {"aid": alliance_id, "st": status}).fetchall()

    return [
        {
            "treaty_id": r[0],
            "treaty_type": r[1],
            "partner_alliance_id": r[2],
            "status": r[3],
            "signed_at": r[4].isoformat() if r[4] else None,
            "partner_name": r[5],
        }
        for r in rows
    ]


@router.post("/treaty/propose")
def propose_treaty_api(payload: TreatyProposal, db: Session = Depends(get_db)):
    """Insert a proposed treaty."""
    columns = ["alliance_id", "partner_alliance_id", "treaty_type", "status"]
    values = [":aid", ":pid", ":type", "'proposed'"]
    params = {
        "aid": payload.proposer_id,
        "pid": payload.partner_alliance_id,
        "type": payload.treaty_type,
    }
    if payload.notes is not None:
        columns.append("notes")
        values.append(":notes")
        params["notes"] = payload.notes
    if payload.end_date is not None:
        columns.append("end_date")
        values.append(":end")
        params["end"] = payload.end_date

    db.execute(
        text(
            f"INSERT INTO alliance_treaties ({', '.join(columns)}) "
            f"VALUES ({', '.join(values)})"
        ),
        params,
    )
    db.commit()
    return {"status": "proposed"}


@router.patch("/treaty/respond")
def respond_treaty_api(payload: TreatyResponse, db: Session = Depends(get_db)):
    """Update treaty status based on a response."""
    status_map = {"accept": "active", "decline": "cancelled"}
    if payload.response not in status_map:
        raise HTTPException(status_code=400, detail="Invalid response")

    db.execute(
        text(
            "UPDATE alliance_treaties SET status = :st, signed_at = now() "
            "WHERE treaty_id = :tid"
        ),
        {"st": status_map[payload.response], "tid": payload.treaty_id},
    )
    db.commit()
    return {"status": status_map[payload.response]}


@router.get("/treaty/{treaty_id}")
def treaty_detail(treaty_id: int, db: Session = Depends(get_db)):
    """Return details for a single treaty."""
    row = db.execute(
        text(
            "SELECT alliance_id, partner_alliance_id, treaty_type, status, signed_at "
            "FROM alliance_treaties WHERE treaty_id = :tid"
        ),
        {"tid": treaty_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Treaty not found")

    return {
        "alliance_id": row[0],
        "partner_alliance_id": row[1],
        "treaty_type": row[2],
        "status": row[3],
        "signed_at": row[4].isoformat() if row[4] else None,
    }
