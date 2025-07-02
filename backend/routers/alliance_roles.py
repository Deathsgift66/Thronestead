"""
Project: Thronestead ©
File: alliance_roles.py
Role: API routes for alliance role management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import Alliance, AllianceRole, User
from services.alliance_service import get_alliance_id

from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance-roles", tags=["alliance_roles"])
alt_router = APIRouter(prefix="/api/alliance/roles", tags=["alliance_roles"])


class RolePayload(BaseModel):
    role_name: str
    can_invite: bool = False
    can_kick: bool = False
    can_manage_resources: bool = False
    can_manage_taxes: bool = False


class RoleUpdatePayload(RolePayload):
    role_id: int


class RoleDeletePayload(BaseModel):
    role_id: int


def ensure_leader(db: Session, user_id: str) -> int:
    """Return the alliance_id if user is the alliance leader."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    alliance = db.query(Alliance).filter(Alliance.alliance_id == user.alliance_id).first()
    if not alliance or alliance.leader != user_id:
        raise HTTPException(status_code=403, detail="Leader permissions required")
    return alliance.alliance_id


@router.get("")
def list_roles(user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    aid = get_alliance_id(db, user_id)
    roles = (
        db.query(AllianceRole)
        .filter(AllianceRole.alliance_id == aid)
        .order_by(AllianceRole.role_id)
        .all()
    )
    return {
        "roles": [
            {
                "role_id": r.role_id,
                "role_name": r.role_name,
                "can_invite": r.can_invite,
                "can_kick": r.can_kick,
                "can_manage_resources": r.can_manage_resources,
                "can_manage_taxes": r.can_manage_taxes,
            }
            for r in roles
        ]
    }


@router.post("/create")
def create_role(
    payload: RolePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = ensure_leader(db, user_id)
    role = AllianceRole(
        alliance_id=aid,
        role_name=payload.role_name,
        can_invite=payload.can_invite,
        can_kick=payload.can_kick,
        can_manage_resources=payload.can_manage_resources,
        can_manage_taxes=payload.can_manage_taxes,
    )
    db.add(role)
    db.commit()
    return {"role_id": role.role_id}


@router.post("/update")
def update_role(
    payload: RoleUpdatePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = ensure_leader(db, user_id)
    role = (
        db.query(AllianceRole)
        .filter(AllianceRole.role_id == payload.role_id)
        .filter(AllianceRole.alliance_id == aid)
        .first()
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role.role_name = payload.role_name
    role.can_invite = payload.can_invite
    role.can_kick = payload.can_kick
    role.can_manage_resources = payload.can_manage_resources
    role.can_manage_taxes = payload.can_manage_taxes
    db.commit()
    return {"status": "updated"}


@router.post("/delete")
def delete_role(
    payload: RoleDeletePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = ensure_leader(db, user_id)
    role = (
        db.query(AllianceRole)
        .filter(AllianceRole.role_id == payload.role_id)
        .filter(AllianceRole.alliance_id == aid)
        .first()
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    return {"status": "deleted"}


# Alt route mappings
# Expose the same endpoints using the alternate prefix
alt_router.include_router(router)
