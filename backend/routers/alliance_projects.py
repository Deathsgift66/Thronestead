from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/alliance-projects", tags=["alliance_projects"])


class ProjectPayload(BaseModel):
    project_id: str | None = None
    progress: int | None = None


@router.get("")
async def list_projects():
    return {"projects": []}


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

