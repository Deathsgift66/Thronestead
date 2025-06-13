from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from .progression_router import get_kingdom_id
from ..security import verify_jwt_token
from services import spies_service

router = APIRouter(prefix="/api/kingdom", tags=["spies"])

class SpyMissionPayload(BaseModel):
    mission: str  # backward compat alias
    mission_type: str | None = None
    target_id: int | None = None


class TrainPayload(BaseModel):
    quantity: int

@router.get("/spies")
def get_spy_info(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    return spies_service.get_spy_record(db, kid)


@router.post("/spies/train")
def train_spies(
    payload: TrainPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    new_count = spies_service.train_spies(db, kid, payload.quantity)
    return {"spy_count": new_count}

@router.post("/spy_missions")
def launch_spy_mission(
    payload: SpyMissionPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    spies_service.start_mission(db, kid)
    mtype = payload.mission_type or payload.mission
    mission_id = spies_service.create_spy_mission(db, kid, mtype, payload.target_id)
    return {"message": "Mission launched", "mission_id": mission_id}

@router.get("/spy_missions")
def list_spy_missions(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    missions = spies_service.list_spy_missions(db, kid)
    return {"missions": missions}

