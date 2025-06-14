# Project Name: Kingmakers Rise©
# File Name: alliance_management.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import Alliance, AllianceMember, AllianceVault, User, KingdomResources
from ..security import verify_jwt_token
from services.audit_service import log_action, log_alliance_activity

router = APIRouter(prefix="/api/alliance", tags=["alliances"])

# Alliance creation cost (can be dynamically loaded from game_settings in future)
CREATE_COST = {"wood": 1000, "stone": 1000, "gold": 500}


class CreatePayload(BaseModel):
    """Payload structure for creating a new alliance."""
    name: str
    region: str | None = None


class DeletePayload(BaseModel):
    """Payload structure for deleting an existing alliance (admin override optional)."""
    alliance_id: int | None = None


@router.post("/create")
def create_alliance(
    payload: CreatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Create a new alliance if the user has no current alliance and enough kingdom resources.
    Deducts resources and registers the user as Leader.
    """
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.kingdom_id:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    if user.alliance_id:
        raise HTTPException(status_code=400, detail="You are already in an alliance.")

    resources = db.query(KingdomResources).filter_by(kingdom_id=user.kingdom_id).first()
    if not resources:
        raise HTTPException(status_code=404, detail="Kingdom resources missing.")

    # Ensure all resource requirements are met
    for res, cost in CREATE_COST.items():
        if getattr(resources, res, 0) < cost:
            raise HTTPException(status_code=400, detail=f"Insufficient {res}")

    # Deduct resources
    for res, cost in CREATE_COST.items():
        setattr(resources, res, getattr(resources, res) - cost)

    # Create Alliance
    alliance = Alliance(
        name=payload.name,
        leader=user_id,
        status="active",
        region=payload.region or user.region,
    )
    db.add(alliance)
    db.flush()  # Assign alliance_id

    # Register the founding member as Leader
    db.add(AllianceMember(
        alliance_id=alliance.alliance_id,
        user_id=user_id,
        username=user.username,
        rank="Leader",
        contribution=0,
        status="active",
    ))

    # Create alliance vault
    db.add(AllianceVault(alliance_id=alliance.alliance_id))

    # Update user record
    user.alliance_id = alliance.alliance_id
    user.alliance_role = "Leader"
    db.commit()

    # Logging
    log_action(db, user_id, "create_alliance", payload.name)
    log_alliance_activity(db, alliance.alliance_id, user_id, "Created", payload.name)

    return {"alliance_id": alliance.alliance_id}


@router.post("/delete")
def delete_alliance(
    payload: DeletePayload | None = None,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Delete an alliance (only allowed by its leader).
    Removes all members, vault, and resets user linkage.
    """
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="No alliance to delete.")

    aid = payload.alliance_id if payload and payload.alliance_id else user.alliance_id
    alliance = db.query(Alliance).filter_by(alliance_id=aid).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    if alliance.leader != user_id:
        raise HTTPException(status_code=403, detail="Only the leader can delete this alliance.")

    # Remove members, vault, and reset user links
    db.query(AllianceMember).filter_by(alliance_id=aid).delete()
    db.query(AllianceVault).filter_by(alliance_id=aid).delete()
    db.query(Alliance).filter_by(alliance_id=aid).delete()

    # Reset all users from that alliance
    for member in db.query(User).filter(User.alliance_id == aid).all():
        member.alliance_id = None
        member.alliance_role = None

    db.commit()

    log_action(db, user_id, "delete_alliance", str(aid))
    return {"status": "deleted"}
