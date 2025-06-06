from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/market", tags=["market"])


class ListingAction(BaseModel):
    listing_id: str


@router.get("/listings")
async def listings():
    return {"listings": []}


@router.get("/my_listings")
async def my_listings():
    return {"listings": []}


@router.post("/cancel_listing")
async def cancel_listing(payload: ListingAction):
    return {"message": "cancelled", "listing": payload.listing_id}


@router.get("/history")
async def history():
    return {"history": []}

