# Project Name: Kingmakers Rise©
# File Name: alliance_projects.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from ..database import get_db
from ..security import verify_jwt_token
from backend.models import (
    Alliance,
    ProjectAllianceCatalogue,
    ProjectsAlliance,
    ProjectsAllianceInProgress,
    ProjectAllianceContribution,
    User,
)

router = APIRouter(prefix="/api/alliance-projects", tags=["alliance_projects"])


class StartPayload(BaseModel):
    project_key: str
    user_id: str


class ContributionPayload(BaseModel):
    project_key: str
    resource_type: str
    amount: int
    user_id: str


def expire_old_projects(db: Session):
    now = datetime.utcnow()
    rows = (
        db.query(ProjectsAllianceInProgress)
        .filter(ProjectsAllianceInProgress.status == "building")
        .filter(ProjectsAllianceInProgress.expected_end < now)
        .all()
    )
    for r in rows:
        r.status = "expired"
    if rows:
        db.commit()


@router.get("/catalogue")
def get_all_catalogue_projects(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ProjectAllianceCatalogue)
        .filter(ProjectAllianceCatalogue.is_active.is_(True))
        .all()
    )
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()}
            for r in rows
        ]
    }


@router.get("/available")
def get_available_projects(
    alliance_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized for this alliance")
    alliance = db.query(Alliance).filter_by(alliance_id=alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    built = (
        db.query(ProjectsAlliance.project_key)
        .filter_by(alliance_id=alliance_id)
        .all()
    )
    active = (
        db.query(ProjectsAllianceInProgress.project_key)
        .filter_by(alliance_id=alliance_id)
        .all()
    )
    exclude = {b[0] for b in built} | {a[0] for a in active}

    rows = (
        db.query(ProjectAllianceCatalogue)
        .filter(ProjectAllianceCatalogue.is_active.is_(True))
        .filter(~ProjectAllianceCatalogue.project_key.in_(exclude))
        .filter(ProjectAllianceCatalogue.requires_alliance_level <= alliance.level)
        .all()
    )
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()}
            for r in rows
        ]
    }


@router.get("/in-progress")
def get_in_progress_projects(
    alliance_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    expire_old_projects(db)
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized for this alliance")
    rows = (
        db.query(ProjectsAllianceInProgress)
        .filter_by(alliance_id=alliance_id)
        .all()
    )
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()}
            for r in rows
        ]
    }


@router.get("/built")
def get_built_projects(
    alliance_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized for this alliance")
    rows = (
        db.query(ProjectsAlliance)
        .filter_by(alliance_id=alliance_id)
        .filter(ProjectsAlliance.build_state == "completed")
        .all()
    )
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()}
            for r in rows
        ]
    }


@router.post("/start")
def start_alliance_project(
    payload: StartPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    expire_old_projects(db)
    if payload.user_id != user_id:
        raise HTTPException(status_code=401, detail="Token mismatch")
    user = db.query(User).filter_by(user_id=payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.alliance_id:
        raise HTTPException(status_code=400, detail="User not in an alliance")

    alliance = db.query(Alliance).filter_by(alliance_id=user.alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    project = (
        db.query(ProjectAllianceCatalogue)
        .filter_by(project_key=payload.project_key)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if alliance.level < (project.requires_alliance_level or 0):
        raise HTTPException(status_code=400, detail="Alliance level too low")

    exists = (
        db.query(ProjectsAlliance.project_id)
        .filter_by(alliance_id=alliance.alliance_id, project_key=payload.project_key)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Project already built")

    any_active = (
        db.query(ProjectsAllianceInProgress.progress_id)
        .filter_by(alliance_id=alliance.alliance_id)
        .filter(ProjectsAllianceInProgress.status == "building")
        .first()
    )
    if any_active:
        raise HTTPException(status_code=400, detail="Another project is active")

    record = ProjectsAllianceInProgress(
        alliance_id=alliance.alliance_id,
        project_key=payload.project_key,
        progress=0,
        started_at=datetime.utcnow(),
        expected_end=datetime.utcnow()
        + timedelta(seconds=project.build_time_seconds or 0),
        status="building",
        built_by=payload.user_id,
    )
    db.add(record)
    db.commit()
    return {"status": "started"}


@router.post("/contribute")
def contribute_to_project(
    payload: ContributionPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    expire_old_projects(db)
    if payload.user_id != user_id:
        raise HTTPException(status_code=401, detail="Token mismatch")
    user = db.query(User).filter_by(user_id=payload.user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="User not in alliance")
    project = (
        db.query(ProjectsAllianceInProgress)
        .filter_by(alliance_id=user.alliance_id, status="building")
        .first()
    )
    if not project or project.project_key != payload.project_key:
        raise HTTPException(status_code=404, detail="No active project")
    contrib = ProjectAllianceContribution(
        alliance_id=user.alliance_id,
        player_name=user.username,
        resource_type=payload.resource_type,
        amount=payload.amount,
        project_key=payload.project_key,
        user_id=payload.user_id,
    )
    project.progress = min(100, project.progress + payload.amount)
    project.last_updated = datetime.utcnow()
    db.add(contrib)
    db.commit()
    return {"status": "ok"}


@router.get("/leaderboard")
def project_leaderboard(
    project_key: str,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    rows = (
        db.query(
            ProjectAllianceContribution.player_name.label("name"),
            func.sum(ProjectAllianceContribution.amount).label("total"),
        )
        .filter(ProjectAllianceContribution.alliance_id == user.alliance_id)
        .filter(ProjectAllianceContribution.project_key == project_key)
        .group_by(ProjectAllianceContribution.player_name)
        .order_by(func.sum(ProjectAllianceContribution.amount).desc())
        .all()
    )
    return {
        "leaderboard": [{"player_name": r.name, "total": r.total} for r in rows]
    }
