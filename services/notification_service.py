# Project Name: Kingmakers Rise©
# File Name: notification_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""Central service for dispatching in-game notifications and real-time messages."""

from __future__ import annotations
import logging
from datetime import datetime

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore

try:
    from backend.supabase_channels import broadcast_notification  # Optional live update support
except ImportError:  # pragma: no cover - fallback when realtime is unavailable
    def broadcast_notification(channel: str, target: str, message: str) -> None:
        """Fallback notifier when Supabase channels are missing."""
        logging.getLogger("KingmakersRise.NotificationFallback").info(
            "[Fallback] %s -> %s: %s", channel, target, message
        )

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# 🔔 Notification Insertion
# ------------------------------------------------------------------------------

def notify_user(
    db: Session,
    user_id: str,
    message: str,
    category: str = "general",
    priority: str = "normal",
    expires_at: datetime | None = None,
) -> None:
    """Send a notification to a user."""
    db.execute(
        text("""
            INSERT INTO user_notifications (
                user_id, message, category, priority, created_at, expires_at
            ) VALUES (
                :uid, :msg, :cat, :pri, now(), :exp
            )
        """),
        {"uid": user_id, "msg": message, "cat": category, "pri": priority, "exp": expires_at},
    )
    db.commit()
    broadcast_notification("user", user_id, message)


def notify_kingdom(
    db: Session,
    kingdom_id: int,
    message: str,
    category: str = "kingdom",
    priority: str = "normal",
    expires_at: datetime | None = None,
) -> None:
    """Send a notification to all users in a kingdom."""
    user_id = db.execute(
        text("SELECT user_id FROM kingdoms WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).scalar()
    if user_id:
        notify_user(db, user_id, message, category, priority, expires_at)


def notify_alliance(
    db: Session,
    alliance_id: int,
    message: str,
    category: str = "alliance",
    priority: str = "normal",
    expires_at: datetime | None = None,
) -> None:
    """Send a notification to all users in an alliance."""
    user_ids = db.execute(
        text("""
            SELECT user_id FROM alliance_members
            WHERE alliance_id = :aid
        """),
        {"aid": alliance_id},
    ).scalars().all()

    for uid in user_ids:
        notify_user(db, uid, message, category, priority, expires_at)


def notify_system_event(
    db: Session,
    message: str,
    tag: str = "system",
) -> None:
    """Log a system-wide message into the global event log."""
    db.execute(
        text("""
            INSERT INTO system_notifications (message, tag, created_at)
            VALUES (:msg, :tag, now())
        """),
        {"msg": message, "tag": tag},
    )
    db.commit()
    logger.info(f"[System Notification] {tag.upper()}: {message}")


# ------------------------------------------------------------------------------
# 📦 Notification Retrieval
# ------------------------------------------------------------------------------

def fetch_user_notifications(
    db: Session,
    user_id: str,
    limit: int = 50,
    include_expired: bool = False
) -> list[dict]:
    """Return recent notifications for a user."""
    query = """
        SELECT id, message, category, priority, created_at, expires_at
        FROM user_notifications
        WHERE user_id = :uid
    """
    if not include_expired:
        query += " AND (expires_at IS NULL OR expires_at > now())"
    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = db.execute(text(query), {"uid": user_id, "limit": limit}).fetchall()
    return [dict(r._mapping) for r in rows]


def clear_user_notifications(db: Session, user_id: str) -> None:
    """Clear all notifications for a user."""
    db.execute(
        text("DELETE FROM user_notifications WHERE user_id = :uid"),
        {"uid": user_id},
    )
    db.commit()


# ------------------------------------------------------------------------------
# 🧪 Testing Hook
# ------------------------------------------------------------------------------

def test_notification_flow(db: Session, user_id: str) -> dict:
    """Create and verify a test notification for the user."""
    notify_user(db, user_id, "Test message from system", category="test")
    return {
        "status": "ok",
        "message": "Test notification sent",
        "user_id": user_id,
        "preview": fetch_user_notifications(db, user_id, limit=1),
    }
