from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/kingdom", tags=["kingdom"])


class ProjectPayload(BaseModel):
    project: str


class ResearchPayload(BaseModel):
    research: str


class QuestPayload(BaseModel):
    quest_id: str


class TemplePayload(BaseModel):
    temple: str


class TrainPayload(BaseModel):
    troop_type: str
    amount: int


@router.post("/start_project")
async def start_project(payload: ProjectPayload):
    return {"message": "Project started", "project": payload.project}


@router.get("/overview")
async def overview():
    return {"overview": "data"}


@router.post("/start_research")
async def start_research(payload: ResearchPayload):
    return {"message": "Research started", "research": payload.research}


@router.post("/accept_quest")
async def accept_quest(payload: QuestPayload):
    return {"message": "Quest accepted", "quest_id": payload.quest_id}


@router.post("/construct_temple")
async def construct_temple(payload: TemplePayload):
    return {"message": "Temple construction started", "temple": payload.temple}


@router.post("/train_troop")
async def train_troop(payload: TrainPayload):
    return {"message": "Training queued", "troop_type": payload.troop_type}

