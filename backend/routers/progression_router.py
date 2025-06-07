from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from ..data import (
    get_max_villages_allowed,
    kingdom_villages,
    military_state,
)

router = APIRouter(prefix="/api/progression", tags=["progression"])

# In-memory store for simple demo purposes
progression_state: dict[str, dict] = {}


def get_user_id(x_user_id: str | None = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")
    return x_user_id


class NoblePayload(BaseModel):
    noble_name: str


class KnightPayload(BaseModel):
    knight_name: str


@router.get("/castle")
def get_castle_level(user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    return {"castle_level": state["castle_level"]}


@router.post("/castle")
def upgrade_castle(user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    state["castle_level"] += 1
    return {"message": "Castle upgraded", "castle_level": state["castle_level"]}


@router.get("/nobles")
def get_nobles(user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    return {"nobles": state["nobles"]}


@router.post("/nobles")
def assign_noble(payload: NoblePayload, user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    state["nobles"].append(payload.noble_name)
    return {"message": "Noble assigned", "nobles": state["nobles"]}


@router.get("/knights")
def get_knights(user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    return {"knights": state["knights"]}


@router.post("/knights")
def assign_knight(payload: KnightPayload, user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    state["knights"].append(payload.knight_name)
    return {"message": "Knight assigned", "knights": state["knights"]}


@router.get("/summary")
def progression_summary(user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    castle_level = state["castle_level"]
    villages = kingdom_villages.get(1, [])
    mil = military_state.setdefault(1, {
        "base_slots": 20,
        "used_slots": 0,
        "morale": 100,
        "queue": [],
        "history": [],
    })
    used = mil["used_slots"]
    return {
        "castle_level": castle_level,
        "max_villages": get_max_villages_allowed(castle_level),
        "current_villages": len(villages),
        "nobles_total": len(state["nobles"]),
        "nobles_available": len(state["nobles"]),
        "knights_total": len(state["knights"]),
        "knights_available": len(state["knights"]),
        "troop_slots": {
            "used": used,
            "available": max(0, mil["base_slots"] - used),
        },
    }

