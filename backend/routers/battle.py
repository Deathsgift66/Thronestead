from fastapi import APIRouter

router = APIRouter(tags=["battle"])


@router.get("/api/battle-resolution")
async def battle_resolution():
    return {"resolution": {}}


@router.get("/api/battle-replay")
async def battle_replay():
    return {"replay": []}

