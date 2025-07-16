# Project Name: Thronestead©
# File Name: alliance_members.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_members.py
Role: API routes for alliance members.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import Alliance, AllianceMember
from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id, require_csrf_token

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


# === Utility ===


MANAGEMENT_ROLES = {"Leader", "Co-Leader", "Officer"}


def validate_management_role(db: Session, user_id: str) -> int:
    row = db.execute(
        text("SELECT alliance_id, alliance_role FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    aid, role = row
    if role not in MANAGEMENT_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return aid


# === ROUTES ===


@router.get("")
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


@router.post("/join")
def join(
    payload: JoinPayload,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
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
    log_action(
        db,
        payload.user_id,
        "join_alliance",
        f"Joined Alliance ID {payload.alliance_id}",
    )
    return {"message": "Joined"}


@router.post("/leave")
def leave(
    payload: MemberAction,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    member = db.query(AllianceMember).filter_by(user_id=payload.user_id).first()
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
def promote(
    payload: RankPayload,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    return _change_rank(payload, db, "Promoted", user_id)


@router.post("/demote")
def demote(
    payload: RankPayload,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    return _change_rank(payload, db, "Demoted", user_id)


def _change_rank(payload: RankPayload, db: Session, action: str, acting_user_id: str):
    aid = validate_management_role(db, acting_user_id)
    member = (
        db.query(AllianceMember)
        .filter_by(
            alliance_id=payload.alliance_id,
            user_id=payload.user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.alliance_id != aid:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    member.rank = payload.new_rank
    db.commit()
    log_action(db, payload.user_id, f"{action.lower()}_rank", payload.new_rank)
    return {"message": action, "user_id": payload.user_id}


@router.post("/remove")
def remove(
    payload: MemberAction,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    aid = validate_management_role(db, user_id)
    member = (
        db.query(AllianceMember)
        .filter_by(
            alliance_id=payload.alliance_id,
            user_id=payload.user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.alliance_id != aid:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    db.delete(member)
    db.commit()
    log_action(db, user_id, "remove_member", f"Removed {payload.user_id}")
    return {"message": "Removed", "user_id": payload.user_id}


@router.post("/contribute")
def contribute(
    payload: ContributionPayload,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    aid = validate_management_role(db, user_id)
    member = db.query(AllianceMember).filter_by(user_id=payload.user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.alliance_id != aid:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    member.contribution += payload.amount
    db.commit()
    return {"message": "Contribution recorded", "total": member.contribution}


@router.post("/apply")
def apply_to_alliance(
    payload: JoinPayload,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
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


@router.post("/approve")
def approve_member(
    payload: MemberAction,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    member = (
        db.query(AllianceMember)
        .filter_by(
            alliance_id=payload.alliance_id,
            user_id=payload.user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.status = "active"
    member.rank = "Member"
    db.commit()
    log_action(db, user_id, "approve_member", f"Approved {payload.user_id}")
    return {"message": "Member approved"}


@router.post("/transfer_leadership")
def transfer_leadership(
    payload: TransferLeadershipPayload,
    user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    alliance = db.query(Alliance).filter_by(alliance_id=payload.alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    if alliance.leader != user_id:
        raise HTTPException(
            status_code=403, detail="Only the current leader can transfer leadership."
        )

    new_leader = (
        db.query(AllianceMember)
        .filter_by(
            alliance_id=payload.alliance_id,
            user_id=payload.new_leader_id,
        )
        .first()
    )
    if not new_leader:
        raise HTTPException(status_code=404, detail="Target member not found")

    current_leader = (
        db.query(AllianceMember)
        .filter_by(
            alliance_id=payload.alliance_id,
            user_id=user_id,
        )
        .first()
    )

    if current_leader:
        current_leader.rank = "Co-Leader"

    new_leader.rank = "Leader"
    alliance.leader = new_leader.user_id
    db.commit()
    log_action(db, user_id, "transfer_leader", f"Transferred to {new_leader.user_id}")
    return {"message": "Leadership transferred", "leader": new_leader.user_id}
