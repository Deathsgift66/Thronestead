from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..data import military_state, recruitable_units

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
    unit_id: int
    quantity: int


def get_state():
    return military_state.setdefault(1, {
        "base_slots": 20,
        "used_slots": 0,
        "morale": 100,
        "queue": [],
        "history": [],
    })


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
    state = get_state()

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    if state["used_slots"] + payload.quantity > state["base_slots"]:
        raise HTTPException(status_code=400, detail="Not enough troop slots")

    unit = next((u for u in recruitable_units if u["id"] == payload.unit_id), None)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    state["used_slots"] += payload.quantity
    state["queue"].append({
        "unit_name": unit["name"],
        "quantity": payload.quantity,
    })

    return {"message": "Training queued", "unit_id": payload.unit_id}

