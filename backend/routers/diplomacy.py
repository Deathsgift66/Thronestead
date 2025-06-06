from fastapi import APIRouter

router = APIRouter(prefix="/api/diplomacy", tags=["diplomacy"])


@router.get("/alliances")
async def alliances():
    return {"alliances": []}


@router.get("/treaties")
async def treaties():
    return {"treaties": []}


@router.get("/conflicts")
async def diplomacy_conflicts():
    return {"conflicts": []}

