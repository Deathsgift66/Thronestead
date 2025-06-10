from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sqlalchemy.sql import func

from ..database import get_db
from ..models import User, PlayerMessage
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/messages", tags=["messages"])


def get_current_user_id(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
) -> str:
    """Authenticate user via JWT headers."""
    return verify_jwt_token(authorization, x_user_id)


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
def send_message(
    payload: MessagePayload,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    recipient = db.query(User).filter(User.username == payload.recipient).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    message = PlayerMessage(
        recipient_id=recipient.user_id,
        user_id=user_id,
        subject=payload.subject,
        message=payload.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"message": "sent", "message_id": message.message_id}


@router.get("/list")
def list_messages(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(PlayerMessage, User.username)
        .join(User, PlayerMessage.user_id == User.user_id)
        .filter(PlayerMessage.recipient_id == user_id)
        .filter(PlayerMessage.deleted_by_recipient.is_(False))
        .order_by(PlayerMessage.sent_at.desc())
        .all()
    )
    return {
        "messages": [
            {
                "message_id": m.message_id,
                "subject": m.subject,
                "message": m.message,
                "sent_at": m.sent_at,
                "is_read": m.is_read,
                "user_id": m.user_id,
                "username": u,
            }
            for m, u in rows
        ]
    }


class DeletePayload(BaseModel):
    message_id: int


@router.post("/delete")
def delete_message(
    payload: DeletePayload,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    msg = (
        db.query(PlayerMessage)
        .filter(PlayerMessage.message_id == payload.message_id,
                PlayerMessage.recipient_id == user_id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.deleted_by_recipient = True
    db.commit()
    return {"status": "deleted"}


@router.get("/{message_id}")
def get_message(
    message_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlayerMessage, User.username)
        .join(User, PlayerMessage.user_id == User.user_id)
        .filter(PlayerMessage.message_id == message_id,
                PlayerMessage.recipient_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")
    msg, username = row
    msg.is_read = True
    msg.last_updated = func.now()
    db.commit()
    return {
        "message_id": msg.message_id,
        "subject": msg.subject,
        "message": msg.message,
        "sent_at": msg.sent_at,
        "user_id": msg.user_id,
        "username": username,
    }

