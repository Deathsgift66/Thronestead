from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/kingdom_military", tags=["kingdom_military"])


class RecruitPayload(BaseModel):
    unit: str
    amount: int


@router.get("/summary")
async def summary():
    return {"summary": {}}


@router.get("/recruitable")
async def recruitable():
    return {"units": []}


@router.post("/recruit")
async def recruit(payload: RecruitPayload):
    return {"message": "Recruiting", "unit": payload.unit}


@router.get("/queue")
async def queue():
    return {"queue": []}


@router.get("/history")
async def history():
    return {"history": []}

