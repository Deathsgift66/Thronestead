"""
Project: Thronestead ©
File: kingdom.py
Role: API routes for kingdom.
Version: 2025-06-21
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action
from services.kingdom_quest_service import start_quest as db_start_quest
from services.kingdom_setup_service import create_kingdom_transaction
from services.research_service import (
    list_research,
    research_overview,
    start_research as db_start_research,
)

from ..data import DEFAULT_REGIONS, recruitable_units
from ..database import get_db
from ..security import verify_jwt_token
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/kingdom", tags=["kingdom"])


# --- Pydantic Models ---
class KingdomCreatePayload(BaseModel):
    kingdom_name: str
    ruler_title: Optional[str]
    village_name: str
    region: str
    banner_image: Optional[str]
    emblem_image: Optional[str]
    motto: Optional[str] = "From Ashes, Kingdoms Rise"


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


class KingdomUpdatePayload(BaseModel):
    ruler_name: Optional[str] = None
    ruler_title: Optional[str] = None
    kingdom_name: Optional[str] = None
    motto: Optional[str] = None
    description: Optional[str] = None
    religion: Optional[str] = None
    region: Optional[str] = None
    banner_url: Optional[str] = None
    emblem_url: Optional[str] = None


# --- Utility ---
def get_troop_state(db: Session, kingdom_id: int):
    row = (
        db.execute(
            text("SELECT * FROM kingdom_troop_slots WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        )
        .mappings()
        .fetchone()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Troop slot state not found")
    return row


# --- Routes ---
@router.get("/regions")
def list_regions(db: Session = Depends(get_db)):
    try:
        rows = (
            db.execute(text("SELECT * FROM region_catalogue ORDER BY region_name"))
            .mappings()
            .fetchall()
        )
        return [dict(r) for r in rows] or DEFAULT_REGIONS
    except Exception:
        return DEFAULT_REGIONS


@router.post("/create")
def create_kingdom(
    payload: KingdomCreatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
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
        db.execute(
            text("INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid)"),
            {"kid": kid},
        )
        db.commit()
        log_action(
            db, user_id, "create_kingdom", f"Kingdom {payload.kingdom_name} created"
        )
        return {"kingdom_id": kid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overview")
def overview(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    kingdom = (
        db.execute(
            text(
                "SELECT kingdom_name, region, created_at FROM kingdoms WHERE kingdom_id = :kid"
            ),
            {"kid": kid},
        )
        .mappings()
        .fetchone()
    )
    if not kingdom:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    resources = (
        db.execute(
            text(
                "SELECT gold, food, wood FROM kingdom_resources WHERE kingdom_id = :kid"
            ),
            {"kid": kid},
        )
        .mappings()
        .fetchone()
        or {}
    )
    state = get_troop_state(db, kid)
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
def summary(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    state = get_troop_state(db, kid)
    return {
        "resources": {"gold": 1000, "food": 500, "wood": 300},
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
    kid = get_kingdom_id(db, user_id)
    try:
        ends_at = db_start_research(db, kid, payload.tech_code)
        log_action(db, user_id, "start_research", payload.tech_code)
        return {
            "message": "Research started",
            "tech_code": payload.tech_code,
            "ends_at": ends_at.isoformat(),
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Tech not found")


@router.get("/research")
def get_research(
    category: Optional[str] = None,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    return {"research": list_research(db, kid, category=category)}


@router.get("/research/list")
def research_list(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    return research_overview(db, kid)


@router.post("/accept_quest")
def accept_quest(
    payload: QuestPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    ends_at = db_start_quest(db, 1, payload.quest_code, user_id)
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
        INSERT INTO kingdom_temples (kingdom_id, temple_name, temple_type, level, is_major, constructed_by)
        VALUES (:kid, :name, :type, 1, :major, :uid)
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
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
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
def train_troop(
    payload: TrainPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    unit = next((u for u in recruitable_units if u["id"] == payload.unit_id), None)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    state = get_troop_state(db, kid)
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    if state["used_slots"] + payload.quantity > state["base_slots"]:
        raise HTTPException(status_code=400, detail="Not enough troop slots")

    db.execute(
        text(
            """
        INSERT INTO training_queue (kingdom_id, unit_id, unit_name, quantity, initiated_by)
        VALUES (:kid, :unit_id, :unit_name, :qty, :uid)
    """
        ),
        {
            "kid": kid,
            "unit_id": payload.unit_id,
            "unit_name": unit["name"],
            "qty": payload.quantity,
            "uid": user_id,
        },
    )
    db.commit()
    return {"message": "Training queued", "unit_id": payload.unit_id}


@router.get("/profile")
def kingdom_profile(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    row = db.execute(
        text(
            """
        SELECT kingdom_id, ruler_name, ruler_title, kingdom_name,
               motto, description, region, banner_url,
               emblem_url, is_on_vacation
        FROM kingdoms WHERE user_id = :uid
    """
        ),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    rel = db.execute(
        text("SELECT religion_name FROM kingdom_religion WHERE kingdom_id = :kid"),
        {"kid": row[0]},
    ).fetchone()
    return {
        "ruler_name": row[1],
        "ruler_title": row[2],
        "kingdom_name": row[3],
        "motto": row[4],
        "description": row[5],
        "region": row[6],
        "banner_url": row[7],
        "emblem_url": row[8],
        "on_vacation": row[9],
        "religion": rel[0] if rel else None,
    }


@router.post("/update")
def update_kingdom_profile(
    payload: KingdomUpdatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"), {"uid": user_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    kid = row[0]

    updates = []
    params = {"kid": kid}
    field_map = {
        "ruler_name": "ruler_name",
        "ruler_title": "ruler_title",
        "kingdom_name": "kingdom_name",
        "motto": "motto",
        "description": "description",
        "region": "region",
        "banner_url": "banner_url",
        "emblem_url": "emblem_url",
    }

    for attr, column in field_map.items():
        value = getattr(payload, attr)
        if value is not None:
            updates.append(f"{column} = :{attr}")
            params[attr] = value

    if updates:
        db.execute(
            text(f"UPDATE kingdoms SET {', '.join(updates)} WHERE kingdom_id = :kid"),
            params,
        )

    if payload.religion is not None:
        db.execute(
            text(
                """
            INSERT INTO kingdom_religion (kingdom_id, religion_name)
            VALUES (:kid, :religion)
            ON CONFLICT (kingdom_id)
            DO UPDATE SET religion_name = EXCLUDED.religion_name
        """
            ),
            {"kid": kid, "religion": payload.religion},
        )

    db.commit()
    return {"message": "updated"}
