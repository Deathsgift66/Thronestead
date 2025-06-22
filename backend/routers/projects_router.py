# Project Name: Thronestead©
# File Name: projects_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""Module docstring."""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.vacation_mode_service import check_vacation_mode
from ..data import castle_progression_state, kingdom_projects

router = APIRouter(prefix="/api/projects", tags=["projects"])


# 🧾 Client payload schema
class ProjectPayload(BaseModel):
    project_code: str
    kingdom_id: int = 1


# 📚 Centralized catalogue of available projects and their requirements
def _get_requirements(code: str) -> dict:
    catalogue = {
        "demo_project": {
            "required_castle_level": 1,
            "required_nobles": 0,
            "required_knights": 0,
            "build_time_seconds": 60,
            "power_score": 10,
        },
        # Add more project entries here as needed
        "watchtower": {
            "required_castle_level": 3,
            "required_nobles": 1,
            "required_knights": 0,
            "build_time_seconds": 300,
            "power_score": 30,
        },
        "barracks_upgrade": {
            "required_castle_level": 5,
            "required_nobles": 2,
            "required_knights": 1,
            "build_time_seconds": 600,
            "power_score": 50,
        },
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


# 🔧 Start a new project for the given kingdom
@router.post("/start", response_model=None)
def start_project(
    payload: ProjectPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    # 🛡 Prevent construction while in vacation mode
    check_vacation_mode(db, payload.kingdom_id)

    # 📋 Fetch project requirement from internal catalogue
    req = _get_requirements(payload.project_code)

    # 🔎 Load current castle progression state
    prog = castle_progression_state.get(
        payload.kingdom_id, {"castle_level": 0, "nobles": 0, "knights": 0}
    )

    # ❌ Validate if the kingdom meets the project prerequisites
    if (
        prog["castle_level"] < req["required_castle_level"]
        or prog["nobles"] < req["required_nobles"]
        or prog["knights"] < req["required_knights"]
    ):
        raise HTTPException(status_code=403, detail="Project requirements not met")

    # 🕒 Calculate project completion time
    now = datetime.utcnow()
    ends_at = now + timedelta(seconds=req["build_time_seconds"])

    # 🧾 Store project in in-memory structure (to be replaced with database in future)
    record = {
        "project_code": payload.project_code,
        "started_at": now.isoformat(),
        "ends_at": ends_at.isoformat(),
        "started_by": user_id,
        "power_score": req["power_score"],
    }
    kingdom_projects.setdefault(payload.kingdom_id, []).append(record)

    return {
        "message": "Project started",
        "project_code": payload.project_code,
        "ends_at": record["ends_at"],
    }


# 📡 Fetch current and in-progress projects for a kingdom
@router.get("/status/{kingdom_id}", response_model=None)
def project_status(
    kingdom_id: int,
    user_id: str = Depends(verify_jwt_token),
):
    return {
        "projects": kingdom_projects.get(kingdom_id, [])
    }
