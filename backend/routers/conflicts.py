from fastapi import APIRouter

router = APIRouter(prefix="/api/conflicts", tags=["conflicts"])


@router.get("/active")
async def active_conflicts():
    return {"conflicts": []}


@router.get("/historical")
async def historical_conflicts():
    return {"conflicts": []}

