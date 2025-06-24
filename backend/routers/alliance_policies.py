# Project Name: Thronestead©
# File Name: alliance_policies.py
# Version: 2025-06-21
# Developer: OpenAI
"""API routes for alliance policy management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import AlliancePolicy, Alliance, User
from services.audit_service import log_alliance_activity

from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance-policies", tags=["alliance_policies"])


# ---------- Utility ----------

def get_alliance_info(user_id: str, db: Session) -> tuple[int, str]:
    """Return the alliance ID and role for a user or raise 403."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    return user.alliance_id, user.alliance_role or "Member"


def require_leader(role: str):
    if role not in {"Leader", "Co-Leader"}:
        raise HTTPException(status_code=403, detail="Leader permission required")


# ---------- Payloads ----------

class PolicyPayload(BaseModel):
    policy_id: int


# ---------- Endpoints ----------

@router.get("/active")
def active_policies(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    """Return active policy IDs for the caller's alliance."""
    aid, _ = get_alliance_info(user_id, db)
    rows = (
        db.query(AlliancePolicy)
        .filter_by(alliance_id=aid, is_active=True)
        .order_by(AlliancePolicy.policy_id)
        .all()
    )
    return {"policies": [r.policy_id for r in rows]}


@router.post("/activate")
def activate_policy(
    payload: PolicyPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, role = get_alliance_info(user_id, db)
    require_leader(role)

    row = (
        db.query(AlliancePolicy)
        .filter_by(alliance_id=aid, policy_id=payload.policy_id)
        .first()
    )
    if row:
        row.is_active = True
    else:
        db.add(
            AlliancePolicy(
                alliance_id=aid, policy_id=payload.policy_id, is_active=True
            )
        )
    db.commit()
    log_alliance_activity(
        db, aid, user_id, "PolicyActivated", str(payload.policy_id)
    )
    return {"status": "activated", "policy_id": payload.policy_id}


@router.post("/deactivate")
def deactivate_policy(
    payload: PolicyPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, role = get_alliance_info(user_id, db)
    require_leader(role)

    row = (
        db.query(AlliancePolicy)
        .filter_by(alliance_id=aid, policy_id=payload.policy_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Policy not found")
    row.is_active = False
    db.commit()
    log_alliance_activity(
        db, aid, user_id, "PolicyDeactivated", str(payload.policy_id)
    )
    return {"status": "deactivated", "policy_id": payload.policy_id}

