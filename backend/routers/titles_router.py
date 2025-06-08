from fastapi import APIRouter, Depends
from pydantic import BaseModel
from .progression_router import get_user_id
from ..data import player_titles, prestige_scores

router = APIRouter(prefix="/api/kingdom", tags=["titles"])

class TitlePayload(BaseModel):
    title: str

@router.get("/titles")
async def list_titles(user_id: str = Depends(get_user_id)):
    return {"titles": player_titles.get(user_id, [])}

@router.post("/titles")
async def award_title(payload: TitlePayload, user_id: str = Depends(get_user_id)):
    titles = player_titles.setdefault(user_id, [])
    if payload.title not in titles:
        titles.append(payload.title)
    return {"message": "Title awarded"}

@router.get("/prestige")
async def get_prestige(user_id: str = Depends(get_user_id)):
    return {"prestige_score": prestige_scores.get(user_id, 0)}

