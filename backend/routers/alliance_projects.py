# Project Name: Thronestead©
# File Name: alliance_projects.py
# Version: 6.13.2025.19.49
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


# ---------- ROUTES ----------

@router.get("/catalogue")
def get_all_catalogue_projects(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return all available project blueprints."""
    rows = db.query(ProjectAllianceCatalogue).filter(ProjectAllianceCatalogue.is_active.is_(True)).all()
    return {"projects": [{col: getattr(r, col) for col in r.__table__.columns.keys()} for r in rows]}


@router.get("/available")
def get_available_projects(alliance_id: int, user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return projects that the alliance can still build."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    alliance = db.query(Alliance).filter_by(alliance_id=alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    built_keys = {row[0] for row in db.query(ProjectsAlliance.project_key).filter_by(alliance_id=alliance_id)}
    active_keys = {row[0] for row in db.query(ProjectsAllianceInProgress.project_key).filter_by(alliance_id=alliance_id)}
    exclude_keys = built_keys | active_keys

    eligible = (
        db.query(ProjectAllianceCatalogue)
        .filter(ProjectAllianceCatalogue.is_active.is_(True))
        .filter(~ProjectAllianceCatalogue.project_key.in_(exclude_keys))
        .filter(ProjectAllianceCatalogue.requires_alliance_level <= alliance.level)
        .all()
    )
    return {"projects": [{col: getattr(r, col) for col in r.__table__.columns.keys()} for r in eligible]}


@router.get("/in_progress")
def get_in_progress_projects(alliance_id: int, user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return projects currently under construction."""
    expire_old_projects(db)
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    rows = db.query(ProjectsAllianceInProgress).filter_by(alliance_id=alliance_id).all()
    return {"projects": [{col: getattr(r, col) for col in r.__table__.columns.keys()} for r in rows]}


@router.get("/completed")
def get_built_projects(alliance_id: int, user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return completed alliance projects."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or user.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    rows = db.query(ProjectsAlliance).filter_by(alliance_id=alliance_id, build_state="completed").all()
    return {"projects": [{col: getattr(r, col) for col in r.__table__.columns.keys()} for r in rows]}


@router.post("/start")
def start_alliance_project(payload: StartPayload, user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Start construction of a new alliance project."""
    expire_old_projects(db)
    if payload.user_id != user_id:
        raise HTTPException(status_code=401, detail="Token mismatch")

    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="User not in alliance")

    alliance = db.query(Alliance).filter_by(alliance_id=user.alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    project = db.query(ProjectAllianceCatalogue).filter_by(project_key=payload.project_key).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if alliance.level < (project.requires_alliance_level or 0):
        raise HTTPException(status_code=400, detail="Alliance level too low")

    if db.query(ProjectsAlliance.project_id).filter_by(alliance_id=alliance.alliance_id, project_key=payload.project_key).first():
        raise HTTPException(status_code=400, detail="Project already built")

    if db.query(ProjectsAllianceInProgress.progress_id).filter_by(alliance_id=alliance.alliance_id, status="building").first():
        raise HTTPException(status_code=400, detail="Another project is active")

    new_project = ProjectsAllianceInProgress(
        alliance_id=alliance.alliance_id,
        project_key=payload.project_key,
        progress=0,
        started_at=datetime.utcnow(),
        expected_end=datetime.utcnow() + timedelta(seconds=project.build_time_seconds or 0),
        status="building",
        built_by=user_id,
    )
    db.add(new_project)
    db.commit()
    return {"status": "started"}


@router.post("/contribute")
def contribute_to_project(payload: ContributionPayload, user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Add contribution to active alliance project."""
    expire_old_projects(db)
    if payload.user_id != user_id:
        raise HTTPException(status_code=401, detail="Token mismatch")

    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="User not in alliance")

    project = db.query(ProjectsAllianceInProgress).filter_by(alliance_id=user.alliance_id, status="building").first()
    if not project or project.project_key != payload.project_key:
        raise HTTPException(status_code=404, detail="No active project")

    project.progress = min(100, project.progress + payload.amount)

    contribution = ProjectAllianceContribution(
        alliance_id=user.alliance_id,
        player_name=user.username,
        resource_type=payload.resource_type,
        amount=payload.amount,
        project_key=payload.project_key,
        user_id=user_id,
    )
    db.add(contribution)
    db.commit()
    return {"status": "ok"}


@router.get("/contributions")
def project_contributions(project_key: str, user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
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
