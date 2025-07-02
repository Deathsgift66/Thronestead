# Project Name: Thronestead©
# File Name: alliance_votes.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""
Project: Thronestead ©
File: alliance_votes.py
Role: API routes for alliance votes and ballots.
Version: 2025-06-21
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from backend.router_utils import mirror_routes
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import AllianceVote, AllianceVoteParticipant
from services.audit_service import log_action, log_alliance_activity
from services.alliance_service import get_alliance_id

from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance-votes", tags=["alliance_votes"])
alt_router = APIRouter(prefix="/api/alliance/votes", tags=["alliance_votes"])


class VoteProposal(BaseModel):
    proposal_type: str
    proposal_details: dict[str, Any]
    vote_type: str = "simple"
    target_id: Optional[int] = None
    ends_at: Optional[datetime] = None
    vote_metadata: Optional[str] = None


class BallotPayload(BaseModel):
    vote_id: int
    choice: str


@router.post("/propose")
def propose_vote(
    payload: VoteProposal,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = get_alliance_id(db, user_id)
    vote = AllianceVote(
        alliance_id=aid,
        proposal_type=payload.proposal_type,
        proposal_details=payload.proposal_details,
        created_by=user_id,
        ends_at=payload.ends_at,
        vote_type=payload.vote_type,
        target_id=payload.target_id,
        vote_metadata=payload.vote_metadata,
    )
    db.add(vote)
    db.commit()
    log_alliance_activity(db, aid, user_id, "Vote Proposed", payload.proposal_type)
    log_action(db, user_id, "Vote Proposed", payload.proposal_type)
    return {"vote_id": vote.vote_id}


@router.post("/vote")
def cast_ballot(
    payload: BallotPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = get_alliance_id(db, user_id)
    vote = db.query(AllianceVote).filter(AllianceVote.vote_id == payload.vote_id).first()
    if not vote or vote.alliance_id != aid:
        raise HTTPException(status_code=404, detail="Vote not found")

    participant = (
        db.query(AllianceVoteParticipant)
        .filter(
            AllianceVoteParticipant.vote_id == payload.vote_id,
            AllianceVoteParticipant.user_id == user_id,
        )
        .first()
    )
    if participant:
        participant.vote_choice = payload.choice
        participant.voted_at = datetime.utcnow()
    else:
        db.add(
            AllianceVoteParticipant(
                vote_id=payload.vote_id,
                user_id=user_id,
                vote_choice=payload.choice,
            )
        )
    db.commit()
    log_alliance_activity(db, aid, user_id, "Vote Cast", str(payload.vote_id))
    log_action(db, user_id, "Vote Cast", str(payload.vote_id))
    return {"status": "voted"}


@router.get("/results/{vote_id}")
def vote_results(
    vote_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = get_alliance_id(db, user_id)
    vote = db.query(AllianceVote).filter(AllianceVote.vote_id == vote_id).first()
    if not vote or vote.alliance_id != aid:
        raise HTTPException(status_code=404, detail="Vote not found")

    rows = (
        db.query(
            AllianceVoteParticipant.vote_choice,
            func.count(AllianceVoteParticipant.vote_choice),
        )
        .filter(AllianceVoteParticipant.vote_id == vote_id)
        .group_by(AllianceVoteParticipant.vote_choice)
        .all()
    )
    results = {choice: count for choice, count in rows}
    total = sum(results.values())
    return {
        "vote_id": vote.vote_id,
        "proposal_type": vote.proposal_type,
        "proposal_details": vote.proposal_details,
        "status": vote.status,
        "results": results,
        "total": total,
    }


mirror_routes(router, alt_router)
