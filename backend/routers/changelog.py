from fastapi import APIRouter

router = APIRouter(prefix="/api/changelog", tags=["changelog"])


@router.get("")
async def changelog():
    return {"entries": []}

