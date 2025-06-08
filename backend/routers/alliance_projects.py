from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import Alliance, ProjectAllianceCatalogue

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
        db.query(ProjectAllianceCatalogue)
        .filter(ProjectAllianceCatalogue.is_active.is_(True))
        .filter(ProjectAllianceCatalogue.requires_alliance_level <= alliance.level)
        .all()
    )

    return {
        "projects": [
            {
                "project_code": r.project_code,
                "project_name": r.project_name,
                "description": r.description,
                "effect_summary": r.effect_summary,
                "resource_costs": r.resource_costs,
                "build_time_seconds": r.build_time_seconds,
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

