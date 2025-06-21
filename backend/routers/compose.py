# Project Name: Thronestead©
# File Name: compose.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from backend.models import PlayerMessage, Notification, War, AllianceNotice
from ..security import verify_jwt_token
from services.audit_service import log_action

router = APIRouter(prefix="/api/compose", tags=["compose"])

# ------------------------------
# Payload Schemas
# ------------------------------

class MessagePayload(BaseModel):
    recipient_id: str
    message: str
    anonymous: bool = False


class NoticePayload(BaseModel):
    title: str
    message: str
    category: str | None = None
    link_action: str | None = None
    alliance_id: int | None = None
    image_url: str | None = None
    expires_at: datetime | None = None


class TreatyPayload(BaseModel):
    partner_alliance_id: int
    treaty_type: str


class WarPayload(BaseModel):
    defender_id: str
    war_reason: str

# ------------------------------
# Message Routes
# ------------------------------

@router.post("/send-message")
@router.post("/message")
def send_message(
    payload: MessagePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Send an in-game message to another player."""
    recipient = db.execute(
        text("SELECT user_id FROM users WHERE user_id = :rid"),
        {"rid": payload.recipient_id},
    ).fetchone()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    msg = PlayerMessage(
        recipient_id=payload.recipient_id,
        user_id=user_id,
        message=payload.message,
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)

    log_action(db, user_id, "send_message", f"To: {payload.recipient_id}")
    return {"status": "sent", "message_id": msg.message_id}
