from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..data import castle_progression_state, kingdom_projects
from ..security import verify_jwt_token
from ..database import get_db
from sqlalchemy.orm import Session
from services.vacation_mode_service import check_vacation_mode

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectPayload(BaseModel):
    project_code: str
    kingdom_id: int = 1


# Placeholder catalogue with requirements
def _get_requirements(code: str):
    catalogue = {
        "demo_project": {
            "required_castle_level": 1,
            "required_nobles": 0,
            "required_knights": 0,
            "build_time_seconds": 60,
            "power_score": 10,
        }
    }
    return catalogue.get(
        code,
        {
            "required_castle_level": 0,
            "required_nobles": 0,
            "required_knights": 0,
            "build_time_seconds": 60,
            "power_score": 0,
        },
    )


@router.post("/start")
async def start_project(
    payload: ProjectPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    check_vacation_mode(db, payload.kingdom_id)
    req = _get_requirements(payload.project_code)
    prog = castle_progression_state.get(
        payload.kingdom_id, {"castle_level": 0, "nobles": 0, "knights": 0}
    )

    if (
        prog["castle_level"] < req["required_castle_level"]
        or prog["nobles"] < req["required_nobles"]
        or prog["knights"] < req["required_knights"]
    ):
        raise HTTPException(status_code=403, detail="Project requirements not met")

    ends_at = datetime.utcnow() + timedelta(seconds=req.get("build_time_seconds", 60))
    record = {
        "project_code": payload.project_code,
        "started_at": datetime.utcnow().isoformat(),
        "ends_at": ends_at.isoformat(),
        "started_by": user_id,
        "power_score": req.get("power_score", 0),
    }
    kingdom_projects.setdefault(payload.kingdom_id, []).append(record)

    return {
        "message": "Project started",
        "project_code": payload.project_code,
        "ends_at": record["ends_at"],
    }


@router.get("/status/{kingdom_id}")
async def project_status(
    kingdom_id: int,
    user_id: str = Depends(verify_jwt_token),
):
    return {"projects": kingdom_projects.get(kingdom_id, [])}

