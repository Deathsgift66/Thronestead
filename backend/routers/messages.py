from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/messages", tags=["messages"])


class MessagePayload(BaseModel):
    recipient: str
    content: str


@router.post("/send")
async def send_message(payload: MessagePayload):
    return {"message": "sent", "recipient": payload.recipient}

