from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id

router = APIRouter(prefix="/api/account-projects", tags=["account_projects"])

class StartPayload(BaseModel):
    project_code: str

@router.post("/start")
def start_project(payload: StartPayload, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    try:
        db.execute(
            text("""
                INSERT INTO projects_player (kingdom_id, project_code, power_score, ends_at)
                VALUES (:kid, :code, 0, NOW())
            """),
            {"kid": kid, "code": payload.project_code},
        )
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Project started", "project_code": payload.project_code}
