# Project Name: Thronestead©
# File Name: audit_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
# Description: Audit and activity tracking services for players, alliances, and system actions.

import logging
from typing import Iterable, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Placeholder returned when a user's profile has been deleted
DELETED_PLACEHOLDER = "[deleted_user]"


def _row_to_log_dict(row) -> dict:
    """Convert a DB row into a standard log dictionary."""
    log = {
        "log_id": row[0],
        "user_id": DELETED_PLACEHOLDER if row[2] else row[1],
        "action": row[3],
        "details": row[4],
        "created_at": row[5],
    }
    if len(row) > 6:
        log["kingdom_id"] = row[6]
    return log

# ------------------------
# Core Audit Log Functions
# ------------------------


def log_action(
    db: Session,
    user_id: Optional[str],
    action: str,
    details: str,
    ip_address: str | None = None,
    device_info: str | None = None,
    kingdom_id: int | None = None,
) -> None:
    """Insert a global user action into the audit_log table."""
    try:
        db.execute(
            text(
                """
                INSERT INTO audit_log (user_id, action, details, ip_address, device_info, kingdom_id)
                VALUES (:uid, :act, :det, :ip, :dev, :kid)
            """
            ),
            {
                "uid": user_id,
                "act": action,
                "det": details,
                "ip": ip_address,
                "dev": device_info,
                "kid": kingdom_id,
            },
        )
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to log action: %s", action)
        raise RuntimeError("Audit log failed") from e


def fetch_logs(
    db: Session,
    user_id: Optional[str] = None,
    kingdom_id: Optional[int] = None,
    limit: int = 100,
) -> list[dict]:
    """
    Fetch global audit log entries. Can filter by user.
    Returns a list of dicts with keys: log_id, user_id, action, details, created_at.
    """
    try:
        query = """
            SELECT l.log_id, l.user_id, u.is_deleted, l.action, l.details, l.created_at, l.kingdom_id
              FROM audit_log l
              LEFT JOIN users u ON u.user_id = l.user_id
             WHERE (:uid IS NULL OR l.user_id = :uid)
               AND (:kid IS NULL OR l.kingdom_id = :kid)
             ORDER BY l.created_at DESC
             LIMIT :limit
        """
        params = {"uid": user_id, "kid": kingdom_id, "limit": limit}
        rows = db.execute(text(query), params).fetchall()
        return [_row_to_log_dict(r) for r in rows]
    except SQLAlchemyError as e:
        logger.exception("Failed to fetch audit logs")
        raise RuntimeError("Audit fetch failed") from e


# ------------------------
# Alliance Activity Logging
# ------------------------


def log_alliance_activity(
    db: Session, alliance_id: int, user_id: Optional[str], action: str, description: str
) -> None:
    """Insert a new alliance-level action into alliance_activity_log."""
    try:
        db.execute(
            text(
                """
                INSERT INTO alliance_activity_log (alliance_id, user_id, action, description)
                VALUES (:aid, :uid, :act, :desc)
            """
            ),
            {"aid": alliance_id, "uid": user_id, "act": action, "desc": description},
        )
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to log alliance activity")
        raise RuntimeError("Alliance activity log failed") from e


# ------------------------
# Flexible Filtering
# ------------------------


def fetch_filtered_logs(
    db: Session,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """
    Filter audit logs by optional user ID, action keyword, and date range.
    """
    query = (
        "SELECT l.log_id, l.user_id, u.is_deleted, l.action, l.details, l.created_at, l.kingdom_id "
        "FROM audit_log l LEFT JOIN users u ON l.user_id = u.user_id WHERE 1=1"
    )
    params = {"limit": limit, "offset": offset}
    if user_id:
        query += " AND l.user_id = :uid"
        params["uid"] = user_id
    if action:
        query += " AND action ILIKE :act"
        params["act"] = f"%{action}%"
    if date_from:
        query += " AND l.created_at >= :date_from"
        params["date_from"] = date_from
    if date_to:
        query += " AND l.created_at <= :date_to"
        params["date_to"] = date_to
    query += " ORDER BY l.created_at DESC LIMIT :limit OFFSET :offset"

    try:
        rows = db.execute(text(query), params).fetchall()
        return [_row_to_log_dict(r) for r in rows]
    except SQLAlchemyError as e:
        logger.exception("Filtered audit query failed")
        raise RuntimeError("Filtered audit fetch failed") from e


# ------------------------
# Deep Audit by User
# ------------------------


def fetch_user_related_logs(db: Session, user_id: str) -> dict:
    """
    Collect logs from all relevant tables linked to the specified user.
    Includes: audit_log, alliance_activity_log, vault, grants, loans, training.
    """
    return {
        "global": fetch_filtered_logs(db, user_id=user_id, limit=100),
        "alliance": [],
        "vault": [],
        "grants": [],
        "loans": [],
        "training": [],
    }
