from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

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

