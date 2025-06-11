from fastapi import APIRouter, Depends, HTTPException, Header
from ..security import verify_jwt_token
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ..database import get_db
from ..models import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationAction(BaseModel):
    notification_id: str | None = None


def get_current_user_id(
    x_user_id: str | None = Header(None),
    authorization: str | None = Header(None)
) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")
    try:
        x_user_id = str(UUID(x_user_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID")
    # verify token matches user when provided
    if authorization:
        verify_jwt_token(authorization=authorization, x_user_id=x_user_id)
    return x_user_id


@router.get("/list")
def list_notifications(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .filter(
            (Notification.expires_at.is_(None))
            | (Notification.expires_at > func.now())
        )
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .all()
    )
    return {
        "notifications": [
            {
                "notification_id": r.notification_id,
                "title": r.title,
                "message": r.message,
                "category": r.category,
                "priority": r.priority,
                "link_action": r.link_action,
                "created_at": r.created_at,
                "is_read": r.is_read,
                "expires_at": r.expires_at,
                "source_system": r.source_system,
                "last_updated": r.last_updated,
            }
            for r in rows
        ]
    }


@router.post("/mark_read")
def mark_read(
    payload: NotificationAction,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(Notification)
        .filter(Notification.notification_id == payload.notification_id,
                Notification.user_id == user_id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    notif.last_updated = func.now()
    db.commit()
    return {"message": "Marked read", "id": payload.notification_id}


@router.post("/mark_all_read")
def mark_all_read(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(Notification.user_id == user_id).update(
        {"is_read": True, "last_updated": func.now()}
    )
    db.commit()
    return {"message": "All marked read"}


@router.post("/clear_all")
def clear_all(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.commit()
    return {"message": "All cleared"}


@router.post("/cleanup_expired")
def cleanup_expired(db: Session = Depends(get_db)):
    deleted = (
        db.query(Notification)
        .filter(Notification.expires_at.is_not(None), Notification.expires_at < func.now())
        .delete()
    )
    db.commit()
    return {"deleted": deleted}

