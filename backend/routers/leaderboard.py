from fastapi import APIRouter

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/{type}")
async def leaderboard(type: str):
    return {"type": type, "leaders": []}

