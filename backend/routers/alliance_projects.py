from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import Alliance, ProjectAllianceCatalogue, ProjectsAlliance

router = APIRouter(prefix="/api/alliance-projects", tags=["alliance_projects"])


class ProjectPayload(BaseModel):
    project_id: str | None = None
    progress: int | None = None


@router.get("")
def list_projects(alliance_id: int = 1, db: Session = Depends(get_db)):
    alliance = db.query(Alliance).filter(Alliance.alliance_id == alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")

    rows = (
        db.query(ProjectsAlliance)
        .filter(ProjectsAlliance.alliance_id == alliance_id)
        .filter(
            (ProjectsAlliance.is_active.is_(True))
            | (ProjectsAlliance.build_state.in_(["queued", "building"]))
        )
        .order_by(ProjectsAlliance.start_time.desc())
        .all()
    )

    return {
        "projects": [
            {
                "project_id": r.project_id,
                "name": r.name,
                "project_key": r.project_key,
                "progress": r.progress,
                "build_state": r.build_state,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "expires_at": r.expires_at,
                "built_by": r.built_by,
                "modifiers": r.modifiers,
            }
            for r in rows
        ]
    }


@router.post("/start")
async def start_project(payload: ProjectPayload):
    return {"message": "Project started", "project_id": payload.project_id}


@router.post("/update")
async def update_project(payload: ProjectPayload):
    return {"message": "Project updated", "project_id": payload.project_id}


@router.get("/contributors")
async def project_contributors():
    return {"contributors": []}


@router.get("/notifications")
async def project_notifications():
    return {"notifications": []}

