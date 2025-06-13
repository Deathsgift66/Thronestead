from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import (
    Alliance,
    AllianceMember,
    AllianceVault,
    User,
    KingdomResources,
)
from ..security import verify_jwt_token
from services.audit_service import log_action, log_alliance_activity

router = APIRouter(prefix="/api/alliance", tags=["alliances"])

CREATE_COST = {"wood": 1000, "stone": 1000, "gold": 500}


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
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.kingdom_id:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    if user.alliance_id:
        raise HTTPException(status_code=400, detail="Already in an alliance")

    resources = (
        db.query(KingdomResources)
        .filter_by(kingdom_id=user.kingdom_id)
        .first()
    )
    if not resources:
        raise HTTPException(status_code=404, detail="Resources not found")

    for res, cost in CREATE_COST.items():
        if getattr(resources, res) < cost:
            raise HTTPException(status_code=400, detail="Insufficient resources")

    for res, cost in CREATE_COST.items():
        setattr(resources, res, getattr(resources, res) - cost)

    alliance = Alliance(
        name=payload.name,
        leader=user_id,
        status="active",
        region=payload.region or user.region,
    )
    db.add(alliance)
    db.flush()

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
    db.add(AllianceVault(alliance_id=alliance.alliance_id))

    user.alliance_id = alliance.alliance_id
    user.alliance_role = "Leader"
    db.commit()

    log_action(db, user_id, "create_alliance", payload.name)
    log_alliance_activity(db, alliance.alliance_id, user_id, "Created", payload.name)

    return {"alliance_id": alliance.alliance_id}


@router.post("/delete")
def delete_alliance(
    payload: DeletePayload | None = None,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="Alliance not found")

    aid = payload.alliance_id if payload and payload.alliance_id else user.alliance_id
    alliance = db.query(Alliance).filter_by(alliance_id=aid).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    if alliance.leader != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.query(AllianceMember).filter_by(alliance_id=aid).delete()
    db.query(AllianceVault).filter_by(alliance_id=aid).delete()
    db.query(Alliance).filter_by(alliance_id=aid).delete()
    for member in db.query(User).filter(User.alliance_id == aid).all():
        member.alliance_id = None
        member.alliance_role = None
    db.commit()

    log_action(db, user_id, "delete_alliance", str(aid))
    return {"status": "deleted"}
