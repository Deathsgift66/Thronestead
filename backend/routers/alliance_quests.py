# Project Name: Kingmakers Rise©
# File Name: alliance_quests.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from backend.models import (
    User,
    QuestAllianceCatalogue,
    QuestAllianceTracking,
    QuestAllianceContribution,
)
from services.audit_service import log_action
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance-quests", tags=["alliance_quests"])


class QuestStartPayload(BaseModel):
    quest_code: str


def get_alliance_info(user_id: str, db: Session) -> tuple[int, str]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return user.alliance_id, user.alliance_role or "Member"


@router.get("/catalogue")
def get_quest_catalogue(db: Session = Depends(get_db)):
    quests = (
        db.query(QuestAllianceCatalogue)
        .filter(QuestAllianceCatalogue.is_active.is_(True))
        .order_by(QuestAllianceCatalogue.quest_code)
        .all()
    )
    return [
        {
            "quest_code": q.quest_code,
            "name": q.name,
            "description": q.description,
            "duration_hours": q.duration_hours,
            "category": q.category,
            "objectives": q.objectives,
            "rewards": q.rewards,
            "required_level": q.required_level,
            "repeatable": q.repeatable,
            "max_attempts": q.max_attempts,
        }
        for q in quests
    ]


@router.get("/available")
def get_available_quests(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, _ = get_alliance_info(user_id, db)
    started = (
        db.query(QuestAllianceTracking.quest_code)
        .filter(QuestAllianceTracking.alliance_id == aid)
        .all()
    )
    codes = [s.quest_code for s in started]
    query = db.query(QuestAllianceCatalogue).filter(QuestAllianceCatalogue.is_active.is_(True))
    if codes:
        query = query.filter(~QuestAllianceCatalogue.quest_code.in_(codes))
    quests = query.all()
    return [
        {
            "quest_code": q.quest_code,
            "name": q.name,
            "description": q.description,
            "duration_hours": q.duration_hours,
            "category": q.category,
            "objectives": q.objectives,
            "rewards": q.rewards,
        }
        for q in quests
    ]


@router.get("/active")
def get_active_quests(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, _ = get_alliance_info(user_id, db)
    rows = (
        db.query(QuestAllianceTracking)
        .filter(QuestAllianceTracking.alliance_id == aid)
        .filter(QuestAllianceTracking.status == "active")
        .all()
    )
    return [
        {
            "quest_code": r.quest_code,
            "status": r.status,
            "progress": r.progress,
            "ends_at": r.ends_at,
            "started_at": r.started_at,
        }
        for r in rows
    ]


@router.get("/completed")
def get_completed_quests(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, _ = get_alliance_info(user_id, db)
    rows = (
        db.query(QuestAllianceTracking)
        .filter(QuestAllianceTracking.alliance_id == aid)
        .filter(QuestAllianceTracking.status == "completed")
        .all()
    )
    return [
        {
            "quest_code": r.quest_code,
            "status": r.status,
            "progress": r.progress,
            "ends_at": r.ends_at,
            "started_at": r.started_at,
        }
        for r in rows
    ]


@router.post("/start")
def start_quest(
    payload: QuestStartPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, role = get_alliance_info(user_id, db)
    if role not in {"Leader", "Co-Leader", "Officer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    quest = (
        db.query(QuestAllianceCatalogue)
        .filter(QuestAllianceCatalogue.quest_code == payload.quest_code)
        .filter(QuestAllianceCatalogue.is_active.is_(True))
        .first()
    )
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    existing = (
        db.query(QuestAllianceTracking)
        .filter(QuestAllianceTracking.alliance_id == aid)
        .filter(QuestAllianceTracking.quest_code == payload.quest_code)
        .first()
    )
    if existing:
        if existing.status == "completed" and quest.repeatable:
            if quest.max_attempts and existing.attempt_count >= quest.max_attempts:
                raise HTTPException(status_code=400, detail="Max attempts reached")
            hours = quest.duration_hours or 0
            existing.status = "active"
            existing.progress = 0
            existing.ends_at = datetime.utcnow() + timedelta(hours=hours)
            existing.started_at = datetime.utcnow()
            existing.started_by = user_id
            db.commit()
            log_action(db, user_id, "Alliance Quest Restarted", payload.quest_code)
            return {"status": "started"}
        raise HTTPException(status_code=400, detail="Quest already started or completed")
    hours = quest.duration_hours or 0
    ends_at = datetime.utcnow() + timedelta(hours=hours)
    tracking = QuestAllianceTracking(
        alliance_id=aid,
        quest_code=payload.quest_code,
        status="active",
        progress=0,
        ends_at=ends_at,
        started_by=user_id,
    )
    db.add(tracking)
    db.commit()
    log_action(db, user_id, "Alliance Quest Started", payload.quest_code)
    return {"status": "started"}


@router.get("/contributions")
def get_contributions(
    quest_code: Optional[str] = Query(None),
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, _ = get_alliance_info(user_id, db)
    query = db.query(QuestAllianceContribution).filter(
        QuestAllianceContribution.alliance_id == aid
    )
    if quest_code:
        query = query.filter(QuestAllianceContribution.quest_code == quest_code)
    rows = query.order_by(QuestAllianceContribution.timestamp.desc()).all()
    return [
        {
            "player_name": r.player_name,
            "resource_type": r.resource_type,
            "amount": r.amount,
            "timestamp": r.timestamp,
            "quest_code": r.quest_code,
            "user_id": str(r.user_id),
        }
        for r in rows
    ]


@router.get("/detail/{quest_code}")
def quest_detail(
    quest_code: str,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return detailed information about a specific alliance quest."""
    aid, _ = get_alliance_info(user_id, db)

    cat = (
        db.query(QuestAllianceCatalogue)
        .filter(QuestAllianceCatalogue.quest_code == quest_code)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Quest not found")

    tracking = (
        db.query(QuestAllianceTracking)
        .filter_by(alliance_id=aid, quest_code=quest_code)
        .first()
    )

    contrib_rows = (
        db.query(QuestAllianceContribution)
        .filter_by(alliance_id=aid, quest_code=quest_code)
        .order_by(QuestAllianceContribution.timestamp.desc())
        .all()
    )

    contributions = [
        {
            "player_name": r.player_name,
            "resource_type": r.resource_type,
            "amount": r.amount,
            "timestamp": r.timestamp,
            "user_id": str(r.user_id),
        }
        for r in contrib_rows
    ]

    return {
        "quest_code": cat.quest_code,
        "name": cat.name,
        "description": cat.description,
        "duration_hours": cat.duration_hours,
        "category": cat.category,
        "objectives": cat.objectives,
        "rewards": cat.rewards,
        "required_level": cat.required_level,
        "repeatable": cat.repeatable,
        "max_attempts": cat.max_attempts,
        "progress": tracking.progress if tracking else None,
        "status": tracking.status if tracking else None,
        "ends_at": tracking.ends_at if tracking else None,
        "started_at": tracking.started_at if tracking else None,
        "contributions": contributions,
    }


class ProgressPayload(BaseModel):
    quest_code: str
    amount: int


@router.post("/progress")
def update_progress(
    payload: ProgressPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, _ = get_alliance_info(user_id, db)
    row = (
        db.query(QuestAllianceTracking)
        .filter_by(alliance_id=aid, quest_code=payload.quest_code)
        .first()
    )
    if not row or row.status != "active":
        raise HTTPException(status_code=404, detail="Quest not active")
    row.progress = min(100, row.progress + payload.amount)
    row.last_updated = datetime.utcnow()
    if row.progress >= 100:
        row.progress = 100
        row.status = "completed"
        row.attempt_count = (row.attempt_count or 0) + 1
        quest = (
            db.query(QuestAllianceCatalogue)
            .filter_by(quest_code=payload.quest_code)
            .first()
        )
        if quest and quest.rewards:
            next_code = quest.rewards.get("unlock_next")
            if next_code:
                next_row = (
                    db.query(QuestAllianceTracking)
                    .filter_by(alliance_id=aid, quest_code=next_code)
                    .first()
                )
                if not next_row:
                    next_quest = (
                        db.query(QuestAllianceCatalogue)
                        .filter_by(quest_code=next_code)
                        .first()
                    )
                    if next_quest:
                        hours = next_quest.duration_hours or 0
                        db.add(
                            QuestAllianceTracking(
                                alliance_id=aid,
                                quest_code=next_code,
                                status="active",
                                progress=0,
                                ends_at=datetime.utcnow()
                                + timedelta(hours=hours),
                                started_by=user_id,
                            )
                        )
    db.commit()
    return {"status": row.status, "progress": row.progress}


class ClaimPayload(BaseModel):
    quest_code: str


@router.post("/claim")
def claim_reward(
    payload: ClaimPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, role = get_alliance_info(user_id, db)
    if role not in {"Leader", "Co-Leader", "Officer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = (
        db.query(QuestAllianceTracking)
        .filter_by(alliance_id=aid, quest_code=payload.quest_code)
        .first()
    )
    if not row or row.status != "completed":
        raise HTTPException(status_code=400, detail="Quest not claimable")
    quest = (
        db.query(QuestAllianceCatalogue)
        .filter_by(quest_code=payload.quest_code)
        .first()
    )
    db.commit()
    log_action(db, user_id, "Alliance Quest Reward Claimed", payload.quest_code)
    return {"status": "claimed", "rewards": quest.rewards if quest else {}}

