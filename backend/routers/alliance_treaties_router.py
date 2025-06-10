from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id
from services.audit_service import log_action, log_alliance_activity

router = APIRouter(prefix="/api/alliance-treaties", tags=["alliance_treaties"])


class ProposePayload(BaseModel):
    treaty_type: str
    partner_alliance_id: int
    notes: str | None = None
    end_date: str | None = None


class RespondPayload(BaseModel):
    treaty_id: int
    action: str


def get_alliance_id(db: Session, user_id: str) -> int:
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]


def validate_alliance_permission(db: Session, user_id: str, permission: str) -> int:
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


@router.get("/my-treaties")
def get_my_treaties(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    aid = get_alliance_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at, end_date, notes
              FROM alliance_treaties
             WHERE alliance_id = :aid OR partner_alliance_id = :aid
             ORDER BY signed_at DESC
            """
        ),
        {"aid": aid},
    ).fetchall()
    return {
        "treaties": [
            {
                "treaty_id": r[0],
                "alliance_id": r[1],
                "treaty_type": r[2],
                "partner_alliance_id": r[3],
                "status": r[4],
                "signed_at": r[5].isoformat() if r[5] else None,
                "end_date": r[6].isoformat() if r[6] else None,
                "notes": r[7],
            }
            for r in rows
        ]
    }


@router.post("/propose")
def propose_treaty(
    payload: ProposePayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    aid = validate_alliance_permission(db, user_id, "can_manage_treaties")
    db.execute(
        text(
            "INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status, notes, end_date) "
            "VALUES (:aid, :type, :pid, 'proposed', :notes, :ed)"
        ),
        {
            "aid": aid,
            "type": payload.treaty_type,
            "pid": payload.partner_alliance_id,
            "notes": payload.notes,
            "ed": payload.end_date,
        },
    )
    db.commit()
    log_alliance_activity(db, aid, user_id, "Treaty Proposed", payload.treaty_type)
    log_action(db, user_id, "Treaty Proposed", payload.treaty_type)
    return {"status": "proposed"}


@router.post("/respond")
def respond_to_treaty(
    payload: RespondPayload,
    user_id: str = Depends(get_user_id),
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

    if payload.action == "accept":
        status = "active"
    elif payload.action == "cancel":
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
    log_alliance_activity(db, aid, user_id, f"Treaty {status.capitalize()}", str(payload.treaty_id))
    log_action(db, user_id, f"Treaty {status}", str(payload.treaty_id))
    return {"status": status}


@router.post("/renew")
def renew_treaty(
    treaty_id: int,
    end_date: str | None = None,
    user_id: str = Depends(get_user_id),
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
    log_alliance_activity(db, aid, user_id, "Treaty Renewed", str(treaty_id))
    log_action(db, user_id, "Treaty Renewed", str(treaty_id))
    return {"status": "renewed"}


@router.get("/view/{treaty_id}")
def view_treaty(
    treaty_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            "SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at, end_date, notes "
            "FROM alliance_treaties WHERE treaty_id = :tid"
        ),
        {"tid": treaty_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Treaty not found")
    aid = get_alliance_id(db, user_id)
    if aid not in (row[1], row[3]):
        raise HTTPException(status_code=403, detail="Not authorized")
    return {
        "treaty_id": row[0],
        "alliance_id": row[1],
        "treaty_type": row[2],
        "partner_alliance_id": row[3],
        "status": row[4],
        "signed_at": row[5].isoformat() if row[5] else None,
        "end_date": row[6].isoformat() if row[6] else None,
        "notes": row[7],
    }
