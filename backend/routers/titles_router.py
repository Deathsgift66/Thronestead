from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id
from services.kingdom_title_service import award_title, list_titles, set_active_title
from ..data import prestige_scores

router = APIRouter(prefix="/api/kingdom", tags=["titles"])


class TitlePayload(BaseModel):
    title: str


class ActiveTitlePayload(BaseModel):
    title: str | None = None


@router.get("/titles")
async def list_titles_endpoint(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    return {"titles": list_titles(db, kid)}


@router.post("/titles")
async def award_title_endpoint(
    payload: TitlePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    award_title(db, kid, payload.title)
    return {"message": "Title awarded"}


@router.post("/active_title")
async def set_active_title_endpoint(
    payload: ActiveTitlePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    set_active_title(db, kid, payload.title)
    return {"message": "Active title updated"}


@router.get("/prestige")
async def get_prestige(user_id: str = Depends(require_user_id)):
    return {"prestige_score": prestige_scores.get(user_id, 0)}
