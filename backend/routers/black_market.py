from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/black-market", tags=["black_market"])


class MarketAction(BaseModel):
    item_id: str
    quantity: int | None = None


@router.get("")
async def get_market():
    return {"listings": []}


@router.post("/buy")
async def buy_item(payload: MarketAction):
    return {"message": "Purchase complete", "item_id": payload.item_id}


@router.post("/place")
async def place_item(payload: MarketAction):
    return {"message": "Listing placed", "item_id": payload.item_id}

