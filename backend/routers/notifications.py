from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json
from ..security import verify_jwt_token, require_user_id
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ..database import get_db
from backend.models import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationAction(BaseModel):
    notification_id: str | None = None




def _serialize_notification(row: Notification) -> dict:
    return {
        "notification_id": row.notification_id,
        "title": row.title,
        "message": row.message,
        "category": row.category,
        "priority": row.priority,
        "link_action": row.link_action,
        "created_at": row.created_at,
        "is_read": row.is_read,
        "expires_at": row.expires_at,
        "source_system": row.source_system,
        "last_updated": row.last_updated,
    }


@router.get("/list")
def list_notifications(
    limit: int | None = None,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Notification)
        .filter(
            (Notification.user_id == user_id)
            | (Notification.user_id.is_(None))
        )
        .filter(
            (Notification.expires_at.is_(None))
            | (Notification.expires_at > func.now())
        )
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
    )
    if limit:
        query = query.limit(limit)
    rows = query.all()
    return {"notifications": [_serialize_notification(r) for r in rows]}


@router.get("/latest")
def latest_notifications(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
    limit: int = 5,
):
    return list_notifications(limit=limit, user_id=user_id, db=db)


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id,
        )
        .delete()
    )
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"deleted": notification_id}


@router.get("/stream")
async def stream_notifications(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Simple long-polling style stream of new notifications."""
    async def event_generator():
        last_check = func.now()
        for _ in range(30):  # ~2.5 minutes
            rows = (
                db.query(Notification)
                .filter(
                    (Notification.user_id == user_id)
                    | (Notification.user_id.is_(None))
                )
                .filter(Notification.last_updated > last_check)
                .all()
            )
            last_check = func.now()
            for r in rows:
                yield f"data: {json.dumps(_serialize_notification(r))}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/mark_read")
def mark_read(
    payload: NotificationAction,
    user_id: str = Depends(require_user_id),
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
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(Notification.user_id == user_id).update(
        {"is_read": True, "last_updated": func.now()}
    )
    db.commit()
    return {"message": "All marked read"}


@router.post("/clear_all")
def clear_all(
    user_id: str = Depends(require_user_id),
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

