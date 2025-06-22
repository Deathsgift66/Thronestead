# Project Name: Thronestead©
# File Name: kingdom_military.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""Module docstring."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..data import military_state, recruitable_units
from ..security import require_user_id

router = APIRouter(prefix="/api/kingdom_military", tags=["kingdom_military"])

# --------------------------
# 📦 Pydantic Payload Models
# --------------------------

class RecruitPayload(BaseModel):
    unit_id: int
    quantity: int


# --------------------------
# 🧠 Utility
# --------------------------

def get_state():
    """Retrieve or initialize kingdom military state. (Currently fixed to kingdom_id=1)"""
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


# --------------------------
# 📊 API Endpoints
# --------------------------

@router.get("/summary", response_model=None)
async def summary(user_id: str = Depends(require_user_id)):
    """
    🧾 Return a summary of military slots and morale.
    """
    state = get_state()
    base = state["base_slots"]
    used = state["used_slots"]
    return {
        "total_troops": used,
        "base_slots": base,
        "used_slots": used,
        "usable_slots": max(0, base - used),
        "morale": state["morale"],
    }


@router.get("/recruitable", response_model=None)
async def recruitable(user_id: str = Depends(require_user_id)):
    """
    📋 Return the list of recruitable unit types.
    """
    return {"units": recruitable_units}


@router.post("/recruit", response_model=None)
async def recruit(payload: RecruitPayload, user_id: str = Depends(require_user_id)):
    """
    ➕ Queue recruitment for the specified unit type.
    """
    state = get_state()

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity requested")

    if state["used_slots"] + payload.quantity > state["base_slots"]:
        raise HTTPException(status_code=400, detail="Not enough available troop slots")

    unit = next((u for u in recruitable_units if u["id"] == payload.unit_id), None)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    state["used_slots"] += payload.quantity
    queued_unit = {
        "unit_name": unit["name"],
        "quantity": payload.quantity,
    }
    state["queue"].append(queued_unit)

    return {"message": "Training queued", "queued": queued_unit}


@router.get("/queue", response_model=None)
async def queue(user_id: str = Depends(require_user_id)):
    """
    📦 View active training queue.
    """
    return {"queue": get_state()["queue"]}


@router.get("/history", response_model=None)
async def history(user_id: str = Depends(require_user_id)):
    """
    📜 View training history.
    """
    return {"history": get_state()["history"]}
