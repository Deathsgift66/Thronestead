from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..data import military_state, recruitable_units
from ..database import get_db
from ..services.research_service import start_research as db_start_research

router = APIRouter(prefix="/api/kingdom", tags=["kingdom"])


class ProjectPayload(BaseModel):
    project: str


class ResearchPayload(BaseModel):
    tech_code: str


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


@router.get("/summary")
async def kingdom_summary():
    state = get_state()
    resources = {
        "gold": 1000,
        "food": 500,
        "wood": 300,
    }
    return {
        "resources": resources,
        "troops": {
            "total": state["used_slots"],
            "slots": {
                "base": state["base_slots"],
                "used": state["used_slots"],
                "available": max(0, state["base_slots"] - state["used_slots"]),
            },
        },
    }


@router.post("/start_research")
async def start_research(
    payload: ResearchPayload,
    db: Session = Depends(get_db),
):
    """Begin research on a technology for kingdom ``1`` (demo)."""
    try:
        ends_at = db_start_research(db, 1, payload.tech_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tech not found")

    return {
        "message": "Research started",
        "tech_code": payload.tech_code,
        "ends_at": ends_at.isoformat(),
    }


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

