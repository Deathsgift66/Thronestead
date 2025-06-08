from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AllianceMember
from services.audit_service import log_action

router = APIRouter(prefix="/api/alliance_members", tags=["alliance_members"])


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


@router.get("")
def list_members(alliance_id: int = 1, db: Session = Depends(get_db)):
    members = (
        db.query(AllianceMember)
        .filter(AllianceMember.alliance_id == alliance_id)
        .order_by(AllianceMember.rank, AllianceMember.contribution.desc())
        .all()
    )
    payload = [
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
    return {"members": payload}


@router.post("/join")
def join(payload: JoinPayload, db: Session = Depends(get_db)):
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
    log_action(
        db,
        payload.user_id,
        "join_alliance",
        f"Joined Alliance ID {payload.alliance_id}",
    )
    return {"message": "Joined"}


@router.post("/leave")
def leave(payload: MemberAction, db: Session = Depends(get_db)):
    member = (
        db.query(AllianceMember)
        .filter(AllianceMember.user_id == payload.user_id)
        .first()
    )
    if member:
        db.delete(member)
        db.commit()
        log_action(
            db,
            payload.user_id,
            "leave_alliance",
            f"Left Alliance ID {payload.alliance_id}",
        )
    return {"message": "Left"}


@router.post("/promote")
def promote(payload: RankPayload, db: Session = Depends(get_db)):
    member = (
        db.query(AllianceMember)
        .filter(
            AllianceMember.alliance_id == payload.alliance_id,
            AllianceMember.user_id == payload.user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.rank = payload.new_rank
    db.commit()
    return {"message": "Promoted", "user_id": payload.user_id}


@router.post("/demote")
def demote(payload: RankPayload, db: Session = Depends(get_db)):
    member = (
        db.query(AllianceMember)
        .filter(
            AllianceMember.alliance_id == payload.alliance_id,
            AllianceMember.user_id == payload.user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.rank = payload.new_rank
    db.commit()
    return {"message": "Demoted", "user_id": payload.user_id}


@router.post("/remove")
def remove(payload: MemberAction, db: Session = Depends(get_db)):
    member = (
        db.query(AllianceMember)
        .filter(
            AllianceMember.alliance_id == payload.alliance_id,
            AllianceMember.user_id == payload.user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"message": "Removed", "user_id": payload.user_id}


@router.post("/contribute")
def contribute(payload: ContributionPayload, db: Session = Depends(get_db)):
    member = db.query(AllianceMember).filter(AllianceMember.user_id == payload.user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.contribution += payload.amount
    db.commit()
    return {"message": "Contribution recorded", "total": member.contribution}


@router.post("/apply")
def apply_to_alliance(payload: JoinPayload, db: Session = Depends(get_db)):
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


@router.post("/approve")
def approve_member(payload: MemberAction, db: Session = Depends(get_db)):
    member = (
        db.query(AllianceMember)
        .filter(
            AllianceMember.alliance_id == payload.alliance_id,
            AllianceMember.user_id == payload.user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.status = "active"
    db.commit()
    return {"message": "Member approved"}

