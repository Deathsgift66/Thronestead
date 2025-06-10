from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..models import PlayerMessage, Notification, War
from ..security import verify_jwt_token
from services.audit_service import log_action

router = APIRouter(prefix="/api/compose", tags=["compose"])


class MessagePayload(BaseModel):
    recipient_id: str
    message: str


class NoticePayload(BaseModel):
    title: str
    message: str
    category: str | None = None
    link_action: str | None = None


class TreatyPayload(BaseModel):
    partner_alliance_id: int
    treaty_type: str


class WarPayload(BaseModel):
    defender_id: str
    war_reason: str


@router.post("/send-message")
def send_message(
    payload: MessagePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT user_id FROM users WHERE user_id = :rid"),
        {"rid": payload.recipient_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Recipient not found")

    msg = PlayerMessage(
        recipient_id=payload.recipient_id,
        user_id=user_id,
        message=payload.message,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    log_action(db, user_id, "send_message", payload.recipient_id)
    return {"status": "sent", "message_id": msg.message_id}


@router.post("/send-notification")
def send_notification(
    payload: NoticePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    users = db.execute(text("SELECT user_id FROM users")).fetchall()
    for (uid,) in users:
        db.add(
            Notification(
                user_id=uid,
                title=payload.title,
                message=payload.message,
                category=payload.category,
                link_action=payload.link_action,
                source_system="compose",
            )
        )
    db.commit()
    log_action(db, user_id, "broadcast_notice", payload.title)
    return {"status": "sent", "count": len(users)}


@router.post("/propose-treaty")
def propose_treaty(
    payload: TreatyPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    aid = row[0]

    db.execute(
        text(
            "INSERT INTO alliance_treaties (alliance_id, treaty_type, partner_alliance_id, status) "
            "VALUES (:aid, :type, :pid, 'proposed')"
        ),
        {"aid": aid, "type": payload.treaty_type, "pid": payload.partner_alliance_id},
    )
    db.commit()
    log_action(db, user_id, "propose_treaty", payload.treaty_type)
    return {"status": "proposed"}


@router.post("/declare-war")
def declare_war(
    payload: WarPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
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
        attacker_name=attacker[0] if attacker else None,
        defender_name=defender[0],
        war_reason=payload.war_reason,
        status="pending",
        submitted_by=user_id,
    )
    db.add(war)
    db.commit()
    db.refresh(war)
    log_action(db, user_id, "declare_war", payload.defender_id)
    return {"status": "pending", "war_id": war.war_id}
