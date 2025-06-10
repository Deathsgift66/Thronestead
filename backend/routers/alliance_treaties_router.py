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
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at
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
            "INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status) "
            "VALUES (:aid, :type, :pid, 'proposed')"
        ),
        {"aid": aid, "type": payload.treaty_type, "pid": payload.partner_alliance_id},
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
