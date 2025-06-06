from fastapi import APIRouter

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/articles")
async def articles():
    return {"articles": []}

