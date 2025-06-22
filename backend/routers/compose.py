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

@router.post("/send-message", response_model=None)
@router.post("/message", response_model=None)
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


# ------------------------------
# Notice Routes
# ------------------------------

@router.post("/notice", response_model=None)
def create_notice(
    payload: NoticePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Create an alliance notice."""

    row = AllianceNotice(
        alliance_id=payload.alliance_id,
        title=payload.title,
        message=payload.message,
        category=payload.category,
        link_action=payload.link_action,
        image_url=payload.image_url,
        expires_at=payload.expires_at,
        created_by=user_id,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    log_action(db, user_id, "create_notice", f"Notice {row.notice_id}")
    return {"status": "created", "notice_id": row.notice_id}


# ------------------------------
# Treaty Routes
# ------------------------------

@router.post("/treaty", response_model=None)
def propose_treaty(
    payload: TreatyPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Propose an alliance treaty."""

    # Determine the proposing user's alliance
    aid = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()

    if not aid:
        raise HTTPException(status_code=400, detail="User has no alliance")

    db.execute(
        text(
            """
            INSERT INTO alliance_treaties (alliance_id, partner_alliance_id, treaty_type, status)
            VALUES (:aid, :pid, :type, 'proposed')
            """
        ),
        {"aid": aid, "pid": payload.partner_alliance_id, "type": payload.treaty_type},
    )
    db.commit()

    log_action(db, user_id, "propose_treaty", payload.treaty_type)
    return {"status": "proposed"}


# ------------------------------
# War Routes
# ------------------------------

@router.post("/war", response_model=None)
def declare_war(
    payload: WarPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Declare a war on another player."""

    war = War(
        attacker_id=user_id,
        defender_id=payload.defender_id,
        war_reason=payload.war_reason,
        status="pending",
        submitted_by=user_id,
    )

    db.add(war)
    db.commit()
    db.refresh(war)

    log_action(db, user_id, "declare_war", f"Defender {payload.defender_id}")
    return {"status": "pending", "war_id": war.war_id}
