# Project Name: Thronestead©
# File Name: notification_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""Central service for dispatching in-game notifications and real-time messages."""

from __future__ import annotations

import logging
from datetime import datetime

from backend.models import Notification
from services.email_service import send_email

from services.sqlalchemy_support import Session, text

try:
    from backend.supabase_channels import (
        broadcast_notification,
    )  # Optional live update support
except ImportError:  # pragma: no cover - fallback when realtime is unavailable

    def broadcast_notification(channel: str, target: str, message: str) -> None:
        """Fallback notifier when Supabase channels are missing."""
        logging.getLogger("Thronestead.NotificationFallback").info(
            "[Fallback] %s -> %s: %s", channel, target, message
        )


logger = logging.getLogger(__name__)

# Message shown to users after successfully resetting their password.
# The appended note directs them to account recovery if the action was
# unauthorized.
PASSWORD_RESET_CONFIRMATION_MESSAGE = (
    "Your password has been securely changed. If this wasn't you, "
    "please visit [Recover Account](/account/recover.html) immediately."
)


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
        text(
            """
            INSERT INTO user_notifications (
                user_id, message, category, priority, created_at, expires_at
            ) VALUES (
                :uid, :msg, :cat, :pri, now(), :exp
            )
        """
        ),
        {
            "uid": user_id,
            "msg": message,
            "cat": category,
            "pri": priority,
            "exp": expires_at,
        },
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
    user_ids = [
        r[0]
        for r in db.execute(
            text("SELECT user_id FROM alliance_members WHERE alliance_id = :aid"),
            {"aid": alliance_id},
        ).fetchall()
    ]

    if not user_ids:
        return

    db.execute(
        text(
            """
            INSERT INTO user_notifications (
                user_id, message, category, priority, created_at, expires_at
            )
            SELECT user_id, :msg, :cat, :pri, now(), :exp
            FROM alliance_members
            WHERE alliance_id = :aid
            """
        ),
        {
            "aid": alliance_id,
            "msg": message,
            "cat": category,
            "pri": priority,
            "exp": expires_at,
        },
    )
    db.commit()

    for uid in user_ids:
        broadcast_notification("user", uid, message)


def notify_system_event(
    db: Session,
    message: str,
    tag: str = "system",
) -> None:
    """Log a system-wide message into the global event log."""
    db.execute(
        text(
            """
            INSERT INTO system_notifications (message, tag, created_at)
            VALUES (:msg, :tag, now())
        """
        ),
        {"msg": message, "tag": tag},
    )
    db.commit()
    logger.info(f"[System Notification] {tag.upper()}: {message}")


def notify_new_login(
    db: Session,
    user_id: str,
    ip_address: str,
    device_info: str,
) -> None:
    """Alert the user when a login occurs from a new IP or device."""
    row = db.execute(
        text(
            """
            SELECT ip_address, device_info
            FROM user_active_sessions
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT 1
        """
        ),
        {"uid": user_id},
    ).fetchone()

    if not row:
        return

    last_ip, last_device = row
    if last_ip == ip_address and last_device == device_info:
        return

    db.add(
        Notification(
            user_id=user_id,
            title="New Login Detected",
            message="Your account was accessed from a new location.",
            category="security",
            priority="high",
            link_action="/account/recover.html",
        )
    )
    db.commit()

    email_row = db.execute(
        text("SELECT email FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if email_row:
        send_email(
            email_row[0],
            subject="New Device Login",
            body=f"IP: {ip_address}\nUser-Agent: {device_info}",
        )


# ------------------------------------------------------------------------------
# 📦 Notification Retrieval
# ------------------------------------------------------------------------------


def fetch_user_notifications(
    db: Session, user_id: str, limit: int = 50, include_expired: bool = False
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

    rows = (
        db.execute(text(query), {"uid": user_id, "limit": limit}).mappings().fetchall()
    )
    return [dict(r) for r in rows]


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
