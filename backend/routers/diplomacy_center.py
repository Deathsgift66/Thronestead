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
# Endpoints
# --------------------

@router.get("/metrics/{alliance_id}")
def alliance_metrics(alliance_id: int, db: Session = Depends(get_db)):
    """Return diplomacy metrics for a specific alliance."""
    row = db.execute(
        text(
            """
            SELECT diplomacy_score,
                   (SELECT COUNT(*)
                      FROM alliance_treaties
                     WHERE (alliance_id = :aid OR partner_alliance_id = :aid)
                       AND status = 'active') AS active_treaties,
                   (SELECT COUNT(*)
                      FROM alliance_wars
                     WHERE (attacker_alliance_id = :aid OR defender_alliance_id = :aid)
                       AND war_status = 'active') AS ongoing_wars
              FROM alliances
             WHERE alliance_id = :aid
            """
        ),
        {"aid": alliance_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Alliance not found")

    return {
        "diplomacy_score": row[0] or 0,
        "active_treaties": row[1] or 0,
        "ongoing_wars": row[2] or 0,
    }


@router.get("/treaties/{alliance_id}")
def list_treaties(
    alliance_id: int,
    status: str | None = Query(None, description="Filter by treaty status"),
    db: Session = Depends(get_db),
):
    """List treaties involving the specified alliance."""
    query = """
        SELECT t.treaty_id,
               t.treaty_type,
               CASE WHEN t.alliance_id = :aid THEN a2.name ELSE a1.name END AS partner_name,
               t.status,
               t.signed_at
          FROM alliance_treaties t
          JOIN alliances a1 ON t.alliance_id = a1.alliance_id
          JOIN alliances a2 ON t.partner_alliance_id = a2.alliance_id
         WHERE t.alliance_id = :aid OR t.partner_alliance_id = :aid
    """
    params = {"aid": alliance_id}
    if status:
        query += " AND t.status = :status"
        params["status"] = status
    query += " ORDER BY t.signed_at DESC"
    rows = db.execute(text(query), params).fetchall()

    return [
        {
            "treaty_id": r[0],
            "treaty_type": r[1],
            "partner_name": r[2],
            "status": r[3],
            "signed_at": r[4].isoformat() if r[4] else None,
            "end_date": None,
        }
        for r in rows
    ]


@router.post("/treaty/propose")
def propose_treaty(
    payload: TreatyProposal,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Propose a new alliance treaty."""
    alliance_id = get_alliance_id(db, user_id)
    if alliance_id != payload.proposer_id:
        raise HTTPException(status_code=403, detail="Alliance mismatch")

    try:
        from services.alliance_treaty_service import propose_treaty as svc_propose

        svc_propose(db, alliance_id, payload.partner_alliance_id, payload.treaty_type)
        log_alliance_activity(db, alliance_id, user_id, "Treaty Proposed", payload.treaty_type)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": "proposed"}


@router.patch("/treaty/respond")
def respond_treaty(
    payload: TreatyResponse,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Respond to a treaty proposal (accept or reject)."""
    aid = get_alliance_id(db, user_id)
    row = db.execute(
        text("SELECT alliance_id, partner_alliance_id FROM alliance_treaties WHERE treaty_id = :tid"),
        {"tid": payload.treaty_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Treaty not found")
    if aid not in row:
        raise HTTPException(status_code=403, detail="Not authorized")

    from services.alliance_treaty_service import accept_treaty, cancel_treaty

    if payload.response == "accept":
        accept_treaty(db, payload.treaty_id)
    elif payload.response in {"reject", "cancel"}:
        cancel_treaty(db, payload.treaty_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid response")

    log_alliance_activity(db, aid, user_id, f"Treaty {payload.response}", str(payload.treaty_id))
    return {"status": payload.response}


@router.post("/renew_treaty")
def renew_treaty(
    treaty_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Renew an existing treaty by expiring the old one and creating a new active record."""
    row = db.execute(
        text("SELECT alliance_id, partner_alliance_id, treaty_type FROM alliance_treaties WHERE treaty_id = :tid"),
        {"tid": treaty_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Treaty not found")

    aid = get_alliance_id(db, user_id)
    if aid not in (row[0], row[1]):
        raise HTTPException(status_code=403, detail="Not authorized")

    db.execute(text("UPDATE alliance_treaties SET status = 'expired' WHERE treaty_id = :tid"), {"tid": treaty_id})
    db.execute(
        text(
            """
            INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status)
            VALUES (:aid, :type, :pid, 'active')
            """
        ),
        {"aid": row[0], "type": row[2], "pid": row[1]},
    )
    db.commit()

    log_alliance_activity(db, aid, user_id, "Treaty Renewed", str(treaty_id))
    return {"status": "renewed"}
