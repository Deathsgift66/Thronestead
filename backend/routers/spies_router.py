from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id
from ..data import spy_missions
from services import spies_service

router = APIRouter(prefix="/api/kingdom", tags=["spies"])

class SpyMissionPayload(BaseModel):
    mission: str
    target_id: int | None = None


class TrainPayload(BaseModel):
    quantity: int

@router.get("/spies")
async def get_spy_info(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    return spies_service.get_spy_record(db, kid)


@router.post("/spies/train")
async def train_spies(
    payload: TrainPayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    new_count = spies_service.train_spies(db, kid, payload.quantity)
    return {"spy_count": new_count}

@router.post("/spy_missions")
async def launch_spy_mission(
    payload: SpyMissionPayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    spies_service.start_mission(db, kid)
    missions = spy_missions.setdefault(kid, [])
    mission_id = len(missions) + 1
    missions.append({"id": mission_id, "mission": payload.mission, "target_id": payload.target_id})
    return {"message": "Mission launched", "mission_id": mission_id}

@router.get("/spy_missions")
async def list_spy_missions(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    return {"missions": spy_missions.get(kid, [])}

