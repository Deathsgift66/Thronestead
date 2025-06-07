from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..data import castle_progression_state

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
        }
    }
    return catalogue.get(code, {"required_castle_level": 0, "required_nobles": 0, "required_knights": 0})


@router.post("/start")
async def start_project(payload: ProjectPayload):
    req = _get_requirements(payload.project_code)
    prog = castle_progression_state.get(payload.kingdom_id, {"castle_level": 0, "nobles": 0, "knights": 0})

    if (
        prog["castle_level"] < req["required_castle_level"]
        or prog["nobles"] < req["required_nobles"]
        or prog["knights"] < req["required_knights"]
    ):
        raise HTTPException(status_code=403, detail="Project requirements not met")

    return {"message": "Project started", "project_code": payload.project_code}
