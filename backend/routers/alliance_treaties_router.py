# Project Name: Thronestead©
# File Name: alliance_treaties_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_treaties_router.py
Role: API routes for alliance treaties router.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Iterable

from services.audit_service import log_action, log_alliance_activity
from services.alliance_service import get_alliance_id

from ..database import get_db
from ..security import require_user_id, require_active_user_id

router = APIRouter(prefix="/api/alliance-treaties", tags=["alliance_treaties"])
alt_router = APIRouter(prefix="/api/alliance/treaties", tags=["alliance_treaties"])


@router.get("/types")
def get_treaty_types(db: Session = Depends(get_db)):
    """Return all treaty types from the catalogue."""
    rows = (
        db.execute(text("SELECT * FROM treaty_type_catalogue ORDER BY treaty_type"))
        .mappings()
        .fetchall()
    )
    return {"types": [dict(r) for r in rows]}


# --- Payload Models ---


class ProposePayload(BaseModel):
    treaty_type: str
    partner_alliance_id: int


class RespondPayload(BaseModel):
    treaty_id: int
    action: str  # "accept" or "cancel"


# --- Utility Methods ---

def has_role(db: Session, user_id: str, alliance_id: int, roles: Iterable[str]) -> bool:
    """Return True if the user has one of ``roles`` in the alliance."""
    row = db.execute(
        text(
            """
            SELECT r.role_name
              FROM alliance_members m
              JOIN alliance_roles r ON m.role_id = r.role_id
             WHERE m.user_id = :uid AND m.alliance_id = :aid
            """
        ),
        {"uid": user_id, "aid": alliance_id},
    ).fetchone()
    return bool(row and row[0] in roles)


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


# --- Endpoints ---


@router.get("/my-treaties")
def get_my_treaties(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    aid = get_alliance_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id,
                   status, signed_at
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
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    aid = validate_alliance_permission(db, user_id, "can_manage_treaties")
    if not has_role(db, user_id, aid, ["Leader", "Elder"]):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Ensure not proposing with self
    if aid == payload.partner_alliance_id:
        raise HTTPException(status_code=400, detail="Cannot propose treaty to self")

    partner = db.execute(
        text("SELECT 1 FROM alliances WHERE alliance_id = :pid AND status = 'active'"),
        {"pid": payload.partner_alliance_id},
    ).fetchone()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner alliance not found")

    dup = db.execute(
        text(
            """
            SELECT 1 FROM alliance_treaties
             WHERE ((alliance_id = :aid AND partner_alliance_id = :pid)
                    OR (alliance_id = :pid AND partner_alliance_id = :aid))
               AND treaty_type = :type
               AND status IN ('proposed', 'active')
            """
        ),
        {"aid": aid, "pid": payload.partner_alliance_id, "type": payload.treaty_type},
    ).fetchone()

    if dup:
        raise HTTPException(status_code=409, detail="Treaty already exists")

    db.execute(
        text(
            """
            INSERT INTO alliance_treaties
                (alliance_id, treaty_type, partner_alliance_id, status)
             VALUES
                (:aid, :type, :pid, 'proposed')
            """
        ),
        {
            "aid": aid,
            "type": payload.treaty_type,
            "pid": payload.partner_alliance_id,
        },
    )
    db.commit()
    log_alliance_activity(db, aid, user_id, "Treaty Proposed", payload.treaty_type)
    log_action(db, user_id, "Treaty Proposed", payload.treaty_type)
    return {"status": "proposed"}


# --------------------
# Alternative REST-style endpoints
# --------------------


@alt_router.post("/propose")
def alt_propose_treaty(
    payload: ProposePayload,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    """Alias for :func:`propose_treaty` using REST-style path."""
    return propose_treaty(payload, user_id, db)


@router.post("/respond")
def respond_to_treaty(
    payload: RespondPayload,
    user_id: str = Depends(require_active_user_id),
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

    if payload.action not in {"accept", "cancel"}:
        raise HTTPException(status_code=400, detail="Invalid action")

    new_status = "active" if payload.action == "accept" else "cancelled"

    db.execute(
        text(
            """
            UPDATE alliance_treaties
               SET status = :st, signed_at = NOW()
             WHERE treaty_id = :tid
        """
        ),
        {"st": new_status, "tid": payload.treaty_id},
    )
    db.commit()
    log_alliance_activity(
        db, aid, user_id, f"Treaty {new_status.title()}", str(payload.treaty_id)
    )
    log_action(db, user_id, f"Treaty {new_status}", str(payload.treaty_id))
    return {"status": new_status}


@router.post("/renew")
def renew_treaty(
    treaty_id: int,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            SELECT alliance_id, partner_alliance_id, treaty_type
              FROM alliance_treaties
             WHERE treaty_id = :tid
        """
        ),
        {"tid": treaty_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Treaty not found")

    aid = get_alliance_id(db, user_id)
    if aid not in (row[0], row[1]):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Expire old treaty
    db.execute(
        text("UPDATE alliance_treaties SET status = 'expired' WHERE treaty_id = :tid"),
        {"tid": treaty_id},
    )

    # Insert renewed
    db.execute(
        text(
            """
            INSERT INTO alliance_treaties
                (alliance_id, treaty_type, partner_alliance_id, status)
             VALUES
                (:aid, :type, :pid, 'active')
            """
        ),
        {"aid": row[0], "type": row[2], "pid": row[1]},
    )
    db.commit()
    log_alliance_activity(db, aid, user_id, "Treaty Renewed", str(treaty_id))
    log_action(db, user_id, "Treaty Renewed", str(treaty_id))
    return {"status": "renewed"}


@router.get("/view/{treaty_id}")
def view_treaty(
    treaty_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id,
                   status, signed_at
              FROM alliance_treaties
             WHERE treaty_id = :tid
            """
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
    }
