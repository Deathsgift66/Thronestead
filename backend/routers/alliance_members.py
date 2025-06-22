# Project Name: Thronestead©
# File Name: alliance_members.py
# Version: 6.13.2025.19.49 (Refined)
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_members.py
Role: API routes for alliance members.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import AllianceMember, Alliance
from services.audit_service import log_action
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance_members", tags=["alliance_members"])


# === Payload Schemas ===

class MemberAction(BaseModel):
    user_id: str
    alliance_id: int = 1


class JoinPayload(BaseModel):
    alliance_id: int
    user_id: str
    username: str


class RankPayload(MemberAction):
    new_rank: str


class ContributionPayload(BaseModel):
    user_id: str
    amount: int


class TransferLeadershipPayload(BaseModel):
    new_leader_id: str
    alliance_id: int = 1


# === ROUTES ===

@router.get("", response_model=None)
def list_members(
    alliance_id: int = 1,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    members = (
        db.query(AllianceMember)
        .filter_by(alliance_id=alliance_id)
        .order_by(AllianceMember.rank, AllianceMember.contribution.desc())
        .all()
    )
    return {
        "members": [
            {
                "user_id": m.user_id,
                "username": m.username,
                "rank": m.rank,
                "contribution": m.contribution,
                "status": m.status,
                "crest": m.crest,
            }
            for m in members
        ]
    }


@router.post("/join", response_model=None)
def join(
    payload: JoinPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    if db.query(AllianceMember).filter_by(user_id=payload.user_id).first():
        raise HTTPException(status_code=400, detail="User already in an alliance.")

    member = AllianceMember(
        alliance_id=payload.alliance_id,
        user_id=payload.user_id,
        username=payload.username,
        rank="Member",
        contribution=0,
        status="active",
    )
    db.add(member)
    db.commit()
    log_action(db, payload.user_id, "join_alliance", f"Joined Alliance ID {payload.alliance_id}")
    return {"message": "Joined"}


@router.post("/leave", response_model=None)
def leave(payload: MemberAction, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    member = db.query(AllianceMember).filter_by(user_id=payload.user_id).first()
    if member:
        db.delete(member)
        db.commit()
        log_action(db, payload.user_id, "leave_alliance", f"Left Alliance ID {payload.alliance_id}")
    return {"message": "Left"}


@router.post("/promote", response_model=None)
def promote(payload: RankPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    return _change_rank(payload, db, "Promoted")


@router.post("/demote", response_model=None)
def demote(payload: RankPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    return _change_rank(payload, db, "Demoted")


def _change_rank(payload: RankPayload, db: Session, action: str):
    member = db.query(AllianceMember).filter_by(
        alliance_id=payload.alliance_id,
        user_id=payload.user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.rank = payload.new_rank
    db.commit()
    log_action(db, payload.user_id, f"{action.lower()}_rank", payload.new_rank)
    return {"message": action, "user_id": payload.user_id}


@router.post("/remove", response_model=None)
def remove(payload: MemberAction, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    member = db.query(AllianceMember).filter_by(
        alliance_id=payload.alliance_id,
        user_id=payload.user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    log_action(db, user_id, "remove_member", f"Removed {payload.user_id}")
    return {"message": "Removed", "user_id": payload.user_id}


@router.post("/contribute", response_model=None)
def contribute(payload: ContributionPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    member = db.query(AllianceMember).filter_by(user_id=payload.user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.contribution += payload.amount
    db.commit()
    return {"message": "Contribution recorded", "total": member.contribution}


@router.post("/apply", response_model=None)
def apply_to_alliance(payload: JoinPayload, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    if db.query(AllianceMember).filter_by(user_id=payload.user_id).first():
        raise HTTPException(status_code=400, detail="Already applied or a member.")

    member = AllianceMember(
        alliance_id=payload.alliance_id,
        user_id=payload.user_id,
        username=payload.username,
        rank="Applicant",
        contribution=0,
        status="pending",
    )
    db.add(member)
    db.commit()
    return {"message": "Application submitted"}


@router.post("/approve", response_model=None)
def approve_member(payload: MemberAction, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    member = db.query(AllianceMember).filter_by(
        alliance_id=payload.alliance_id,
        user_id=payload.user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.status = "active"
    member.rank = "Member"
    db.commit()
    log_action(db, user_id, "approve_member", f"Approved {payload.user_id}")
    return {"message": "Member approved"}


@router.post("/transfer_leadership", response_model=None)
def transfer_leadership(
    payload: TransferLeadershipPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    alliance = db.query(Alliance).filter_by(alliance_id=payload.alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    if alliance.leader != user_id:
        raise HTTPException(status_code=403, detail="Only the current leader can transfer leadership.")

    new_leader = db.query(AllianceMember).filter_by(
        alliance_id=payload.alliance_id,
        user_id=payload.new_leader_id,
    ).first()
    if not new_leader:
        raise HTTPException(status_code=404, detail="Target member not found")

    current_leader = db.query(AllianceMember).filter_by(
        alliance_id=payload.alliance_id,
        user_id=user_id,
    ).first()

    if current_leader:
        current_leader.rank = "Co-Leader"

    new_leader.rank = "Leader"
    alliance.leader = new_leader.user_id
    db.commit()
    log_action(db, user_id, "transfer_leader", f"Transferred to {new_leader.user_id}")
    return {"message": "Leadership transferred", "leader": new_leader.user_id}
