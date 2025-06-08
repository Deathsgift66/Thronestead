from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id
from ..data import kingdom_spies, spy_missions

router = APIRouter(prefix="/api/kingdom", tags=["spies"])

class SpyMissionPayload(BaseModel):
    mission: str
    target_id: int | None = None

@router.get("/spies")
async def get_spy_info(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    return kingdom_spies.get(kid, {"level": 1, "count": 0})

@router.post("/spy_missions")
async def launch_spy_mission(
    payload: SpyMissionPayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    missions = spy_missions.setdefault(kid, [])
    mission_id = len(missions) + 1
    missions.append({"id": mission_id, "mission": payload.mission, "target_id": payload.target_id})
    return {"message": "Mission launched", "mission_id": mission_id}

@router.get("/spy_missions")
async def list_spy_missions(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    return {"missions": spy_missions.get(kid, [])}

