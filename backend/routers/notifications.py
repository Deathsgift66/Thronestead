# Project Name: Thronestead©
# File Name: notifications.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: notifications.py
Role: API routes for notifications.
Version: 2025-06-21
"""

import asyncio
import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from backend.models import Notification

from ..database import get_db
from ..security import require_user_id
from ..env_utils import get_env_var

# Streaming configuration constants
# Allow tuning via environment variables for easier production scaling
_interval = get_env_var("NOTIFICATION_STREAM_INTERVAL")
STREAM_INTERVAL = int(_interval) if _interval else 5
_cycles = get_env_var("NOTIFICATION_MAX_CYCLES")
MAX_STREAM_CYCLES = int(_cycles) if _cycles else 30

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ---------- Models ----------


class NotificationAction(BaseModel):
    notification_id: str | None = None


# ---------- Internal Utilities ----------


def _serialize_notification(row: Notification) -> dict:
    """Convert Notification ORM object to JSON-serializable dict."""
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


def _base_query(db: Session, user_id: str):
    """Return the base query for notifications visible to ``user_id``."""
    return db.query(Notification).filter(
        (Notification.user_id == user_id) | (Notification.user_id.is_(None))
    )


# ---------- Endpoints ----------


@router.get("/list")
def list_notifications(
    limit: int | None = None,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return all active notifications visible to the current user."""
    query = (
        _base_query(db, user_id)
        .filter(
            (Notification.expires_at.is_(None)) | (Notification.expires_at > func.now())
        )
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
    )

    if limit is not None:
        if limit <= 0 or limit > 100:
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 100"
            )
        query = query.limit(limit)

    rows = query.all()
    return {"notifications": [_serialize_notification(r) for r in rows]}


@router.get("/latest")
def latest_notifications(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
    limit: int = 5,
):
    """Shortcut for retrieving the most recent few notifications."""
    return list_notifications(limit=limit, user_id=user_id, db=db)


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Delete a specific notification for the user."""
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
    return {"message": "Notification deleted", "id": notification_id}


@router.get("/stream", response_class=StreamingResponse)
async def stream_notifications(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Stream new notifications using long polling (SSE style).

    Polls every ``STREAM_INTERVAL`` seconds for up to ``MAX_STREAM_CYCLES``
    iterations. Both values can be tuned via environment variables to better
    support real-time traffic.
    """

    async def event_generator():
        """Yield new notifications or periodic keep-alive pings."""
        last_check = datetime.utcnow()
        cycles = 0
        while cycles < MAX_STREAM_CYCLES:
            rows = (
                _base_query(db, user_id)
                .filter(Notification.last_updated > last_check)
                .order_by(Notification.created_at)
                .all()
            )
            last_check = datetime.utcnow()
            if rows:
                for row in rows:
                    yield f"data: {json.dumps(_serialize_notification(row))}\n\n"
            else:
                # Send SSE ping when no updates to keep connection alive
                yield ": ping\n\n"
            cycles += 1
            await asyncio.sleep(STREAM_INTERVAL)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/mark_read")
def mark_read(
    payload: NotificationAction,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Mark a specific notification as read."""
    notif = (
        db.query(Notification)
        .filter(
            Notification.notification_id == payload.notification_id,
            Notification.user_id == user_id,
        )
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
    """Mark all notifications for the user as read."""
    db.query(Notification).filter(Notification.user_id == user_id).update(
        {"is_read": True, "last_updated": func.now()}
    )
    db.commit()
    return {"message": "All marked as read"}


@router.post("/clear_all")
def clear_all(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Delete all notifications for the user."""
    db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.commit()
    return {"message": "All notifications cleared"}


@router.post("/cleanup_expired")
def cleanup_expired(db: Session = Depends(get_db)):
    """Clean up expired notifications (admin/cron endpoint)."""
    deleted = (
        db.query(Notification)
        .filter(
            Notification.expires_at.is_not(None), Notification.expires_at < func.now()
        )
        .delete()
    )
    db.commit()
    return {"message": "Expired notifications cleaned", "deleted": deleted}
