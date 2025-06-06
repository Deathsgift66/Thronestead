from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/alliance-quests", tags=["alliance_quests"])


class QuestPayload(BaseModel):
    quest_id: str
    contribution: int | None = None


@router.post("/start")
async def start_quest(payload: QuestPayload):
    return {"message": "Quest started", "quest_id": payload.quest_id}


@router.post("/accept")
async def accept_quest(payload: QuestPayload):
    return {"message": "Quest accepted", "quest_id": payload.quest_id}


@router.get("")
async def list_quests(status: str | None = None):
    return {"quests": [], "status": status}


@router.post("/contribute")
async def contribute(payload: QuestPayload):
    return {"message": "Contribution recorded", "quest_id": payload.quest_id}

