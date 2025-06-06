from fastapi import APIRouter

router = APIRouter(prefix="/api/alliance-wars", tags=["alliance_wars"])


@router.get("")
async def list_wars():
    return {"wars": []}


@router.get("/custom-board")
async def custom_board():
    return {"board": []}

