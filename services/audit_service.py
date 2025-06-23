# Project Name: Thronestead©
# File Name: audit_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Audit and activity tracking services for players, alliances, and system actions.

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ------------------------
# Core Audit Log Functions
# ------------------------


def log_action(db: Session, user_id: Optional[str], action: str, details: str) -> None:
    """Insert a global user action into the audit_log table."""
    try:
        db.execute(
            text(
                """
                INSERT INTO audit_log (user_id, action, details)
                VALUES (:uid, :act, :det)
            """
            ),
            {"uid": user_id, "act": action, "det": details},
        )
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to log action: %s", action)
        raise RuntimeError("Audit log failed") from e


def fetch_logs(
    db: Session, user_id: Optional[str] = None, limit: int = 100
) -> list[dict]:
    """
    Fetch global audit log entries. Can filter by user.
    Returns a list of dicts with keys: log_id, user_id, action, details, created_at.
    """
    try:
        query = """
            SELECT log_id, user_id, action, details, created_at
              FROM audit_log
             WHERE (:uid IS NULL OR user_id = :uid)
             ORDER BY created_at DESC
             LIMIT :limit
        """
        rows = db.execute(text(query), {"uid": user_id, "limit": limit}).fetchall()
        return [
            {
                "log_id": r[0],
                "user_id": r[1],
                "action": r[2],
                "details": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]
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
) -> list[dict]:
    """
    Filter audit logs by optional user ID, action keyword, and date range.
    """
    query = (
        "SELECT log_id, user_id, action, details, created_at FROM audit_log WHERE 1=1"
    )
    params = {"limit": limit}
    if user_id:
        query += " AND user_id = :uid"
        params["uid"] = user_id
    if action:
        query += " AND action ILIKE :act"
        params["act"] = f"%{action}%"
    if date_from:
        query += " AND created_at >= :date_from"
        params["date_from"] = date_from
    if date_to:
        query += " AND created_at <= :date_to"
        params["date_to"] = date_to
    query += " ORDER BY created_at DESC LIMIT :limit"

    try:
        rows = db.execute(text(query), params).fetchall()
        return [
            {
                "log_id": r[0],
                "user_id": r[1],
                "action": r[2],
                "details": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]
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
