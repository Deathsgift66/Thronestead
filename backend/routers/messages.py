from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, PlayerMessage

router = APIRouter(prefix="/api/messages", tags=["messages"])


class MessagePayload(BaseModel):
    recipient: str
    subject: str | None = None
    content: str
    sender_id: str | None = None


@router.post("/send")
def send_message(payload: MessagePayload, db: Session = Depends(get_db)):
    recipient = db.query(User).filter(User.username == payload.recipient).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    message = PlayerMessage(
        recipient_id=recipient.user_id,
        user_id=payload.sender_id,
        subject=payload.subject,
        message=payload.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"message": "sent", "message_id": message.message_id}

