# Project Name: Kingmakers Rise©
# File Name: kingdom.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from ..database import get_db
from ..security import require_user_id, verify_jwt_token
from services.kingdom_setup_service import create_kingdom_transaction
from services.research_service import start_research as db_start_research, list_research
from services.kingdom_quest_service import start_quest as db_start_quest
from .progression_router import get_kingdom_id
from ..data import military_state, recruitable_units, DEFAULT_REGIONS

router = APIRouter(prefix="/api/kingdom", tags=["kingdom"])

# --- Pydantic Models ---
class ProjectPayload(BaseModel):
    project: str

class ResearchPayload(BaseModel):
    tech_code: str

class QuestPayload(BaseModel):
    quest_code: str

class TemplePayload(BaseModel):
    temple_type: str
    temple_name: Optional[str] = None
    is_major: bool = False

class TrainPayload(BaseModel):
    unit_id: int
    quantity: int

class KingdomCreatePayload(BaseModel):
    kingdom_name: str
    ruler_title: Optional[str]
    village_name: str
    region: str
    banner_image: Optional[str]
    emblem_image: Optional[str]
    motto: Optional[str] = "From Ashes, Kingdoms Rise"


# --- Core State Utility ---
def get_state():
    return military_state.setdefault(
        1, {
            "base_slots": 20,
            "used_slots": 0,
            "morale": 100,
            "queue": [],
            "history": [],
        }
    )


# --- Routes ---
@router.get("/regions")
def list_regions(db: Session = Depends(get_db)):
    """Return all available regions, fallback to default list if DB query fails."""
    try:
        rows = db.execute(text("SELECT * FROM region_catalogue ORDER BY region_name")).mappings().fetchall()
    except SQLAlchemyError:
        rows = []
    return JSONResponse(content=[dict(r) for r in rows] or DEFAULT_REGIONS)


@router.post("/create")
def create_kingdom(
    payload: KingdomCreatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Create a new kingdom with starter data."""
    try:
        kid = create_kingdom_transaction(
            db=db,
            user_id=user_id,
            kingdom_name=payload.kingdom_name,
            region=payload.region,
            village_name=payload.village_name,
            ruler_title=payload.ruler_title,
            banner_image=payload.banner_image,
            emblem_image=payload.emblem_image,
            motto=payload.motto,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"kingdom_id": kid}


@router.get("/overview")
def overview(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return basic kingdom overview information."""
    kid = get_kingdom_id(db, user_id)

    kingdom = db.execute(
        text(
            "SELECT kingdom_name, region, created_at FROM kingdoms WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).mappings().fetchone()
    if not kingdom:
        raise HTTPException(status_code=404, detail="Kingdom not found")

    resources = db.execute(
        text(
            "SELECT gold, food, wood FROM kingdom_resources WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).mappings().fetchone() or {}

    state = get_state()
    return {
        "kingdom": dict(kingdom),
        "resources": dict(resources),
        "troop_slots": {
            "base": state["base_slots"],
            "used": state["used_slots"],
            "available": max(0, state["base_slots"] - state["used_slots"]),
        },
    }


@router.get("/summary")
def kingdom_summary():
    """Return resource and troop summary."""
    state = get_state()
    return {
        "resources": {
            "gold": 1000,
            "food": 500,
            "wood": 300,
        },
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
def start_research(
    payload: ResearchPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Begin research on a technology."""
    try:
        kid = get_kingdom_id(db, user_id)
        ends_at = db_start_research(db, kid, payload.tech_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tech not found")
    return {"message": "Research started", "tech_code": payload.tech_code, "ends_at": ends_at.isoformat()}


@router.get("/research")
def get_research(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return all research projects for the kingdom."""
    kid = get_kingdom_id(db, user_id)
    return {"research": list_research(db, kid)}


@router.post("/accept_quest")
def accept_quest(
    payload: QuestPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Start a kingdom quest."""
    try:
        ends_at = db_start_quest(db, 1, payload.quest_code, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Quest not found")
    return {"message": "Quest accepted", "quest_code": payload.quest_code, "ends_at": ends_at.isoformat()}


@router.post("/construct_temple")
def construct_temple(
    payload: TemplePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Construct a new temple in the kingdom."""
    kid = get_kingdom_id(db, user_id)
    db.execute(
        text("""
            INSERT INTO kingdom_temples (
                kingdom_id, temple_name, temple_type, level, is_major, constructed_by
            ) VALUES (
                :kid, :name, :type, 1, :major, :uid
            )
        """),
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
def list_temples(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """List all constructed temples for the kingdom."""
    kid = get_kingdom_id(db, user_id)
    rows = db.execute(
        text("SELECT * FROM kingdom_temples WHERE kingdom_id = :kid ORDER BY temple_id"),
        {"kid": kid},
    ).mappings().fetchall()
    return {"temples": [dict(r) for r in rows]}


@router.post("/train_troop")
def train_troop(payload: TrainPayload):
    """Queue training for a unit."""
    state = get_state()

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    if state["used_slots"] + payload.quantity > state["base_slots"]:
        raise HTTPException(status_code=400, detail="Not enough troop slots")

    unit = next((u for u in recruitable_units if u["id"] == payload.unit_id), None)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    state["used_slots"] += payload.quantity
    state["queue"].append({"unit_name": unit["name"], "quantity": payload.quantity})

    return {"message": "Training queued", "unit_id": payload.unit_id}
