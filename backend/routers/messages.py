from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, PlayerMessage
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/messages", tags=["messages"])


class MessagePayload(BaseModel):
    recipient: str
    subject: str | None = None
    content: str
    sender_id: str | None = None


@router.get("/inbox")
def list_inbox(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(PlayerMessage, User.username.label("sender"))
        .join(User, User.user_id == PlayerMessage.user_id)
        .filter(
            PlayerMessage.recipient_id == user_id,
            PlayerMessage.deleted_by_recipient.is_(False),
        )
        .order_by(PlayerMessage.sent_at.desc())
        .limit(100)
        .all()
    )
    messages = [
        {
            "message_id": r.PlayerMessage.message_id,
            "subject": r.PlayerMessage.subject,
            "message": r.PlayerMessage.message,
            "sent_at": r.PlayerMessage.sent_at,
            "is_read": r.PlayerMessage.is_read,
            "sender": r.sender,
        }
        for r in rows
    ]
    return {"messages": messages}


@router.get("/view/{message_id}")
def view_message(
    message_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlayerMessage, User.username.label("sender"))
        .join(User, User.user_id == PlayerMessage.user_id)
        .filter(
            PlayerMessage.message_id == message_id,
            PlayerMessage.recipient_id == user_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")

    row.PlayerMessage.is_read = True
    db.commit()

    msg = row.PlayerMessage
    return {
        "message_id": msg.message_id,
        "subject": msg.subject,
        "message": msg.message,
        "sent_at": msg.sent_at,
        "is_read": msg.is_read,
        "sender": row.sender,
    }


@router.post("/delete/{message_id}")
def delete_message(
    message_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlayerMessage)
        .filter(
            PlayerMessage.message_id == message_id,
            PlayerMessage.recipient_id == user_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")
    row.deleted_by_recipient = True
    db.commit()
    return {"status": "deleted", "message_id": message_id}


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

