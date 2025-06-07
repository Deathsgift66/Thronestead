from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationAction(BaseModel):
    notification_id: str | None = None


def get_current_user_id(x_user_id: str | None = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")
    return x_user_id


@router.get("/list")
def list_notifications(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
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
    db.commit()
    return {"message": "Marked read", "id": payload.notification_id}


@router.post("/mark_all_read")
def mark_all_read(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(Notification.user_id == user_id).update(
        {"is_read": True}
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

