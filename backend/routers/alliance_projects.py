# Project Name: Thronestead©
# File Name: alliance_projects.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_projects.py
Role: API routes for alliance projects.
Version: 2025-06-21
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
import re
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.models import (
    Alliance,
    ProjectAllianceCatalogue,
    ProjectAllianceContribution,
    ProjectsAlliance,
    ProjectsAllianceInProgress,
    User,
)

from ..database import get_db
from ..security import verify_jwt_token, require_csrf_token

router = APIRouter(prefix="/api/alliance/projects", tags=["alliance_projects"])


# ---------- SCHEMA DEFINITIONS ----------


class StartPayload(BaseModel):
    project_key: str
    user_id: str


class ContributionPayload(BaseModel):
    project_key: str
    resource_type: str
    amount: int
    user_id: str


# ---------- UTILITIES ----------


def expire_old_projects(db: Session):
    """Mark any outdated projects as expired."""
    now = datetime.utcnow()
    expired = (
        db.query(ProjectsAllianceInProgress)
        .filter(ProjectsAllianceInProgress.status == "building")
        .filter(ProjectsAllianceInProgress.expected_end < now)
        .all()
    )
    for project in expired:
        project.status = "expired"
    if expired:
        db.commit()


def validate_alliance_permission(db: Session, user_id: str, permission: str) -> int:
    """Return the alliance_id if the user has ``permission`` or raise 403."""
    row = db.execute(
        text(
            """
            SELECT m.alliance_id, r.permissions
              FROM alliance_members m
              JOIN alliance_roles r ON m.role_id = r.role_id
             WHERE m.user_id = :uid
            """
        ),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Not authorized")
    alliance_id, perms = row
    if not perms or permission not in perms:
        raise HTTPException(status_code=403, detail="Permission required")
    return alliance_id


# ---------- ROUTES ----------


@router.get("/catalogue")
def get_all_catalogue_projects(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    """Return all available project blueprints."""
    rows = db.query(ProjectAllianceCatalogue).filter_by(is_active=True).all()
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()} for r in rows
        ]
    }


@router.get("/available")
def get_available_projects(
    alliance_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return projects that the alliance can still build."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    alliance = db.query(Alliance).filter_by(alliance_id=alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    built_keys = {
        r[0]
        for r in db.query(ProjectsAlliance.project_key).filter_by(
            alliance_id=alliance_id
        )
    }
    active_keys = {
        r[0]
        for r in db.query(ProjectsAllianceInProgress.project_key).filter_by(
            alliance_id=alliance_id
        )
    }
    exclude_keys = built_keys | active_keys

    eligible = (
        db.query(ProjectAllianceCatalogue)
        .filter_by(is_active=True)
        .filter(~ProjectAllianceCatalogue.project_key.in_(exclude_keys))
        .filter(ProjectAllianceCatalogue.requires_alliance_level <= alliance.level)
        .all()
    )
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()}
            for r in eligible
        ]
    }


@router.get("/in_progress")
def get_in_progress_projects(
    alliance_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return projects currently under construction."""
    expire_old_projects(db)
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    rows = db.query(ProjectsAllianceInProgress).filter_by(alliance_id=alliance_id).all()
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()} for r in rows
        ]
    }


@router.get("/completed")
def get_built_projects(
    alliance_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return completed alliance projects."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    rows = (
        db.query(ProjectsAlliance)
        .filter_by(alliance_id=alliance_id, build_state="completed")
        .all()
    )
    return {
        "projects": [
            {col: getattr(r, col) for col in r.__table__.columns.keys()} for r in rows
        ]
    }


@router.post("/start")
def start_alliance_project(
    payload: StartPayload,
    csrf: str = Depends(require_csrf_token),
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Start construction of a new alliance project."""
    expire_old_projects(db)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", payload.project_key or ""):
        raise HTTPException(status_code=400, detail="Invalid project key")
    if payload.user_id != user_id:
        raise HTTPException(status_code=401, detail="Token mismatch")

    alliance_id = validate_alliance_permission(db, user_id, "can_manage_projects")

    alliance = db.query(Alliance).filter_by(alliance_id=alliance_id).first()
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

    if (
        db.query(ProjectsAlliance.project_id)
        .filter_by(alliance_id=alliance.alliance_id, project_key=payload.project_key)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Project already built")

    if (
        db.query(ProjectsAllianceInProgress.progress_id)
        .filter_by(alliance_id=alliance.alliance_id, project_key=payload.project_key, status="building")
        .first()
    ):
        raise HTTPException(status_code=400, detail="Project already in progress")

    if (
        db.query(ProjectsAllianceInProgress.progress_id)
        .filter_by(alliance_id=alliance.alliance_id, status="building")
        .first()
    ):
        raise HTTPException(status_code=400, detail="Another project is active")

    recent = (
        db.query(ProjectsAllianceInProgress.progress_id)
        .filter(ProjectsAllianceInProgress.alliance_id == alliance.alliance_id)
        .filter(ProjectsAllianceInProgress.started_at > datetime.utcnow() - timedelta(seconds=5))
        .first()
    )
    if recent:
        raise HTTPException(status_code=429, detail="Project start cooldown")

    new_project = ProjectsAllianceInProgress(
        alliance_id=alliance.alliance_id,
        project_key=payload.project_key,
        progress=0,
        started_at=datetime.utcnow(),
        expected_end=datetime.utcnow()
        + timedelta(seconds=project.build_time_seconds or 0),
        status="building",
        built_by=user_id,
    )
    db.add(new_project)
    db.commit()
    return {"status": "started"}


@router.post("/contribute")
def contribute_to_project(
    payload: ContributionPayload,
    csrf: str = Depends(require_csrf_token),
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Add contribution to active alliance project."""
    expire_old_projects(db)
    if payload.user_id != user_id:
        raise HTTPException(status_code=401, detail="Token mismatch")

    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="User not in alliance")

    project = (
        db.query(ProjectsAllianceInProgress)
        .filter_by(alliance_id=user.alliance_id, status="building")
        .first()
    )
    if not project or project.project_key != payload.project_key:
        raise HTTPException(status_code=404, detail="No active project")

    project.progress = min(100, project.progress + payload.amount)

    db.add(
        ProjectAllianceContribution(
            alliance_id=user.alliance_id,
            user_id=user_id,
            player_name=user.username,
            project_key=payload.project_key,
            resource_type=payload.resource_type,
            amount=payload.amount,
        )
    )
    db.commit()
    return {"status": "ok"}


@router.get("/contributions")
def project_contributions(
    project_key: str,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return contribution totals for a given project."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    rows = (
        db.query(
            ProjectAllianceContribution.player_name.label("name"),
            func.sum(ProjectAllianceContribution.amount).label("total"),
        )
        .filter_by(alliance_id=user.alliance_id, project_key=project_key)
        .group_by(ProjectAllianceContribution.player_name)
        .order_by(func.sum(ProjectAllianceContribution.amount).desc())
        .all()
    )
    return {"contributions": [{"player_name": r.name, "amount": r.total} for r in rows]}
