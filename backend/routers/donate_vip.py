from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/stripe", tags=["donate_vip"])


class CheckoutPayload(BaseModel):
    tier: int


@router.post("/create-checkout-session")
async def create_checkout(payload: CheckoutPayload):
    return {"session_url": "https://example.com"}

