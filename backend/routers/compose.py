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

# ------------------------------
# Broadcast Notification
# ------------------------------

@router.post("/send-notification")
def send_notification(
    payload: NoticePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Send a system-wide notification to all players."""
    users = db.execute(text("SELECT user_id FROM users")).fetchall()

    for (uid,) in users:
        db.add(Notification(
            user_id=uid,
            title=payload.title,
            message=payload.message,
            category=payload.category or "system",
            link_action=payload.link_action,
            source_system="compose",
        ))

    db.commit()
    log_action(db, user_id, "broadcast_notice", f"Title: {payload.title}")
    return {"status": "sent", "count": len(users)}


@router.post("/notice")
def create_notice(
    payload: NoticePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Create an alliance or system notice."""
    notice = AllianceNotice(
        alliance_id=payload.alliance_id,
        title=payload.title,
        message=payload.message,
        category=payload.category,
        link_action=payload.link_action,
        image_url=payload.image_url,
        expires_at=payload.expires_at,
        created_by=user_id,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    log_action(db, user_id, "create_notice", f"Notice ID {notice.notice_id}")
    return {"status": "created", "notice_id": notice.notice_id}

# ------------------------------
# Propose Treaty (Alliance)
# ------------------------------

@router.post("/propose-treaty")
@router.post("/treaty")
def propose_treaty(
    payload: TreatyPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Submit a new treaty proposal from your alliance."""
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="You are not in an alliance.")

    db.execute(
        text(
            """
            INSERT INTO alliance_treaties
            (alliance_id, treaty_type, partner_alliance_id, status)
            VALUES (:aid, :type, :pid, 'proposed')
        """
        ),
        {
            "aid": row[0],
            "type": payload.treaty_type,
            "pid": payload.partner_alliance_id,
        },
    )

    db.commit()
    log_action(db, user_id, "propose_treaty", f"Type: {payload.treaty_type}")
    return {"status": "proposed"}

# ------------------------------
# Declare War (Kingdom)
# ------------------------------

@router.post("/declare-war")
@router.post("/war")
def declare_war(
    payload: WarPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Declare war on another kingdom."""
    attacker = db.execute(
        text("SELECT username FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()

    defender = db.execute(
        text("SELECT username FROM users WHERE user_id = :did"),
        {"did": payload.defender_id},
    ).fetchone()

    if not defender:
        raise HTTPException(status_code=404, detail="Defender not found")

    war = War(
        attacker_id=user_id,
        defender_id=payload.defender_id,
        attacker_name=attacker[0] if attacker else "Unknown",
        defender_name=defender[0],
        war_reason=payload.war_reason,
        status="pending",
        submitted_by=user_id,
    )

    db.add(war)
    db.commit()
    db.refresh(war)

    log_action(db, user_id, "declare_war", f"Against: {payload.defender_id}")
    return {"status": "pending", "war_id": war.war_id}
