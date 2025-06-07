from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..data import castle_progression_state, kingdom_villages, get_max_villages_allowed

router = APIRouter(prefix="/api/villages", tags=["villages"])


class VillagePayload(BaseModel):
    village_name: str
    kingdom_id: int = 1


@router.post("/create")
async def create_village(payload: VillagePayload):
    prog = castle_progression_state.setdefault(
        payload.kingdom_id,
        {"castle_level": 1, "nobles": 0, "knights": 0},
    )

    castle_level = prog.get("castle_level", 1)
    max_allowed = get_max_villages_allowed(castle_level)

    villages = kingdom_villages.setdefault(payload.kingdom_id, [])

    if len(villages) >= max_allowed:
        raise HTTPException(status_code=403, detail="Village limit reached")

    if prog.get("nobles", 0) < 1:
        raise HTTPException(status_code=403, detail="Not enough nobles")

    prog["nobles"] -= 1
    village_id = len(villages) + 1
    village = {"village_id": village_id, "village_name": payload.village_name}
    villages.append(village)

    return {"message": "Village created", "village_id": village_id}
