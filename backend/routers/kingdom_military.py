from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from ..data import military_state, recruitable_units


def get_current_user_id(x_user_id: str | None = Header(None)) -> str:
    """Require X-User-ID header for authentication."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")
    return x_user_id

router = APIRouter(prefix="/api/kingdom_military", tags=["kingdom_military"])


class RecruitPayload(BaseModel):
    unit_id: int
    quantity: int


def get_state():
    # For this demo there is only kingdom_id 1
    return military_state.setdefault(1, {
        "base_slots": 20,
        "used_slots": 0,
        "morale": 100,
        "queue": [],
        "history": [],
    })


@router.get("/summary")
async def summary(user_id: str = Depends(get_current_user_id)):
    state = get_state()
    base = state["base_slots"]
    used = state["used_slots"]
    usable = max(0, base - used)

    return {
        "total_troops": used,
        "base_slots": base,
        "used_slots": used,
        "morale": state["morale"],
        "usable_slots": usable,
    }


@router.get("/recruitable")
async def recruitable(user_id: str = Depends(get_current_user_id)):
    return {"units": recruitable_units}


@router.post("/recruit")
async def recruit(payload: RecruitPayload, user_id: str = Depends(get_current_user_id)):
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

    return {"message": "Training queued"}


@router.get("/queue")
async def queue(user_id: str = Depends(get_current_user_id)):
    state = get_state()
    return {"queue": state["queue"]}


@router.get("/history")
async def history(user_id: str = Depends(get_current_user_id)):
    state = get_state()
    return {"history": state["history"]}

