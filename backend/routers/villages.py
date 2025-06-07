from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..data import kingdom_villages_state

router = APIRouter(prefix="/api/villages", tags=["villages"])


class CreateVillagePayload(BaseModel):
    kingdom_id: int = 1
    village_name: str


@router.post("/create")
async def create_village(payload: CreateVillagePayload):
    state = kingdom_villages_state.setdefault(payload.kingdom_id, {
        "castle_level": 1,
        "max_villages_allowed": 1,
        "nobles": 0,
        "villages": [],
    })

    castle_level = state.get("castle_level", 1)
    max_allowed = state.get("max_villages_allowed", 1)
    current_count = len(state.get("villages", []))

    if current_count >= max_allowed:
        raise HTTPException(status_code=400, detail="Max villages reached")

    if state.get("nobles", 0) < 1:
        raise HTTPException(status_code=400, detail="Not enough Nobles")

    state["nobles"] -= 1
    village_id = current_count + 1
    village = {
        "village_id": village_id,
        "village_name": payload.village_name,
    }
    state["villages"].append(village)

    return {
        "message": "Village created",
        "village": village,
        "castle_level": castle_level,
        "remaining_nobles": state["nobles"],
    }
