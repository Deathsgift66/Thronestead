# Project Name: Thronestead©
# File Name: alliance_bank.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""API routes for alliance bank grants."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import AllianceGrant, User
from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance-bank", tags=["alliance_bank"])


class GrantPayload(BaseModel):
    recipient_user_id: str
    resource_type: str
    amount: int
    due_date: Optional[datetime] = None
    reason: Optional[str] = None


MANAGEMENT_ROLES = {"Leader", "Co-Leader", "Officer"}


def get_alliance_info(user_id: str, db: Session) -> tuple[int, str]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    return user.alliance_id, user.alliance_role or "Member"


@router.post("/grants")
def create_grant(
    payload: GrantPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, role = get_alliance_info(user_id, db)
    if role not in MANAGEMENT_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    grant = AllianceGrant(
        alliance_id=alliance_id,
        recipient_user_id=payload.recipient_user_id,
        resource_type=payload.resource_type,
        amount=payload.amount,
        due_date=payload.due_date,
        reason=payload.reason,
        status="active",
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)
    log_action(
        db,
        user_id,
        "create_grant",
        f"Granted {payload.amount} {payload.resource_type} to {payload.recipient_user_id}",
    )
    return {"grant_id": grant.grant_id}


@router.get("/grants")
def list_grants(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    alliance_id, _ = get_alliance_info(user_id, db)
    rows = db.query(AllianceGrant).filter_by(alliance_id=alliance_id).all()
    return {
        "grants": [
            {
                "grant_id": g.grant_id,
                "recipient_user_id": str(g.recipient_user_id),
                "resource_type": g.resource_type,
                "amount": g.amount,
                "due_date": g.due_date.isoformat() if g.due_date else None,
                "amount_repaid": g.amount_repaid,
                "status": g.status,
            }
            for g in rows
        ]
    }
