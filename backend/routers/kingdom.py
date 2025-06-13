from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from sqlalchemy.exc import SQLAlchemyError
from ..data import military_state, recruitable_units, DEFAULT_REGIONS
from ..database import get_db
from services.research_service import start_research as db_start_research
from services.research_service import list_research
from services.kingdom_quest_service import start_quest as db_start_quest
from services.kingdom_setup_service import create_kingdom_transaction
from .progression_router import get_user_id, get_kingdom_id
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/kingdom", tags=["kingdom"])


class ProjectPayload(BaseModel):
    project: str


class ResearchPayload(BaseModel):
    tech_code: str


class QuestPayload(BaseModel):
    quest_code: str


class TemplePayload(BaseModel):
    temple_type: str
    temple_name: str | None = None
    is_major: bool | None = False


class TrainPayload(BaseModel):
    unit_id: int
    quantity: int


class KingdomCreatePayload(BaseModel):
    kingdom_name: str
    ruler_title: str | None = None
    village_name: str
    region: str
    banner_image: str | None = None
    emblem_image: str | None = None
    motto: str | None = None


@router.get("/regions")
def list_regions(db: Session = Depends(get_db)):
    try:
        rows = (
            db.execute(
                text(
                    "SELECT * FROM region_catalogue ORDER BY region_name"
                )
            )
            .mappings()
            .fetchall()
        )
    except SQLAlchemyError:
        rows = []

    regions = [dict(r) for r in rows] or DEFAULT_REGIONS

    return JSONResponse(content=regions)


@router.post("/create")
def create_kingdom(
    payload: KingdomCreatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    try:
        kid = create_kingdom_transaction(
            db,
            user_id,
            payload.kingdom_name,
            payload.region,
            payload.village_name,
            payload.ruler_title,
            payload.banner_image,
            payload.emblem_image,
            payload.motto or "From Ashes, Kingdoms Rise",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"kingdom_id": kid}


def get_state():
    return military_state.setdefault(
        1,
        {
            "base_slots": 20,
            "used_slots": 0,
            "morale": 100,
            "queue": [],
            "history": [],
        },
    )


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
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Begin research on a technology for the authenticated kingdom."""
    try:
        kid = get_kingdom_id(db, user_id)
        ends_at = db_start_research(db, kid, payload.tech_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tech not found")

    return {
        "message": "Research started",
        "tech_code": payload.tech_code,
        "ends_at": ends_at.isoformat(),
    }


@router.get("/research")
async def get_research(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return research tracking data for the authenticated kingdom."""
    kid = get_kingdom_id(db, user_id)
    records = list_research(db, kid)
    return {"research": records}


@router.post("/accept_quest")
async def accept_quest(
    payload: QuestPayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    try:
        ends_at = db_start_quest(db, 1, payload.quest_code, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Quest not found")

    return {
        "message": "Quest accepted",
        "quest_code": payload.quest_code,
        "ends_at": ends_at.isoformat(),
    }


@router.post("/construct_temple")
def construct_temple(
    payload: TemplePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    db.execute(
        text(
            """
            INSERT INTO kingdom_temples (
                kingdom_id, temple_name, temple_type, level, is_major, constructed_by
            ) VALUES (
                :kid, :name, :type, 1, :major, :uid
            )
            """
        ),
        {
            "kid": kid,
            "name": payload.temple_name or payload.temple_type,
            "type": payload.temple_type,
            "major": payload.is_major,
            "uid": user_id,
        },
    )
    db.commit()
    return {"message": "Temple construction started"}


@router.get("/temples")
def list_temples(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    rows = (
        db.execute(
            text(
                "SELECT * FROM kingdom_temples WHERE kingdom_id = :kid ORDER BY temple_id"
            ),
            {"kid": kid},
        )
        .mappings()
        .fetchall()
    )
    return {"temples": [dict(r) for r in rows]}


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
    state["queue"].append(
        {
            "unit_name": unit["name"],
            "quantity": payload.quantity,
        }
    )

    return {"message": "Training queued", "unit_id": payload.unit_id}
