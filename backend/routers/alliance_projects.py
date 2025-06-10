from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import (
    Alliance,
    ProjectAllianceCatalogue,
    ProjectsAlliance,
    ProjectsAllianceInProgress,
    User,
)

router = APIRouter(prefix="/api/alliance-projects", tags=["alliance_projects"])


class StartPayload(BaseModel):
    project_key: str
    user_id: str


@router.get("/catalogue")
def get_all_catalogue_projects(db: Session = Depends(get_db)):
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
def get_available_projects(alliance_id: int, db: Session = Depends(get_db)):
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
        .filter(~ProjectAllianceCatalogue.project_code.in_(exclude))
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
def get_in_progress_projects(alliance_id: int, db: Session = Depends(get_db)):
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
def get_built_projects(alliance_id: int, db: Session = Depends(get_db)):
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
def start_alliance_project(payload: StartPayload, db: Session = Depends(get_db)):
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
        .filter_by(project_code=payload.project_key)
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

    active = (
        db.query(ProjectsAllianceInProgress.progress_id)
        .filter_by(alliance_id=alliance.alliance_id, project_key=payload.project_key)
        .first()
    )
    if active:
        raise HTTPException(status_code=400, detail="Project already in progress")

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
