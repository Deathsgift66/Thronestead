# Project Name: Thronestead©
# File Name: alliance_management.py
# Version: 6.13.2025.19.49 (Polished)
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_management.py
Role: API routes for alliance management.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import (
    Alliance,
    AllianceMember,
    AllianceVault,
    KingdomResources,
    User,
)
from services.audit_service import log_action, log_alliance_activity

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/alliance", tags=["alliances"])

# 🧮 Alliance creation cost constants
CREATE_COST = {
    "wood": 1000,
    "stone": 1000,
    "gold": 500,
}


class CreatePayload(BaseModel):
    name: str
    region: str | None = None


class DeletePayload(BaseModel):
    alliance_id: int | None = None


@router.post("/create")
def create_alliance(
    payload: CreatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Create a new alliance if the user has no current alliance and enough kingdom resources."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.kingdom_id:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    if user.alliance_id:
        raise HTTPException(status_code=400, detail="You are already in an alliance.")

    resources = db.query(KingdomResources).filter_by(kingdom_id=user.kingdom_id).first()
    if not resources:
        raise HTTPException(status_code=404, detail="Kingdom resources missing.")

    # ✅ Check resource sufficiency
    for res, cost in CREATE_COST.items():
        if getattr(resources, res, 0) < cost:
            raise HTTPException(status_code=400, detail=f"Insufficient {res}")

    # 🔻 Deduct resource cost
    for res, cost in CREATE_COST.items():
        setattr(resources, res, getattr(resources, res) - cost)

    # 🏰 Create alliance
    alliance = Alliance(
        name=payload.name,
        leader=user_id,
        status="active",
        region=payload.region or user.region,
    )
    db.add(alliance)
    db.flush()  # Assigns `alliance_id`

    # 🧑 Add founding member as Leader
    db.add(
        AllianceMember(
            alliance_id=alliance.alliance_id,
            user_id=user_id,
            username=user.username,
            rank="Leader",
            contribution=0,
            status="active",
        )
    )

    # 💰 Initialize vault
    db.add(AllianceVault(alliance_id=alliance.alliance_id))

    # 🔗 Link user
    user.alliance_id = alliance.alliance_id
    user.alliance_role = "Leader"

    db.commit()

    # 📝 Log
    log_action(db, user_id, "create_alliance", payload.name)
    log_alliance_activity(db, alliance.alliance_id, user_id, "Created", payload.name)

    return {"alliance_id": alliance.alliance_id}


@router.post("/delete")
def delete_alliance(
    payload: DeletePayload | None = None,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Delete an alliance (only allowed by its leader)."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="No alliance to delete.")

    aid = payload.alliance_id if payload and payload.alliance_id else user.alliance_id
    alliance = db.query(Alliance).filter_by(alliance_id=aid).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    if alliance.leader != user_id:
        raise HTTPException(
            status_code=403, detail="Only the leader can delete this alliance."
        )

    # 🚫 Remove members and vault
    db.query(AllianceMember).filter_by(alliance_id=aid).delete()
    db.query(AllianceVault).filter_by(alliance_id=aid).delete()
    db.query(Alliance).filter_by(alliance_id=aid).delete()

    # 🔄 Reset affected users
    for member in db.query(User).filter(User.alliance_id == aid).all():
        member.alliance_id = None
        member.alliance_role = None

    db.commit()

    # 📝 Log
    log_action(db, user_id, "delete_alliance", str(aid))
    return {"status": "deleted"}
