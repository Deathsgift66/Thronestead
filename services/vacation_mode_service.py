# Project Name: Kingmakers Rise©
# File Name: vacation_mode_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Handles logic for entering, exiting, and enforcing vacation mode for kingdoms.

from __future__ import annotations
from datetime import datetime, timedelta
import logging

from fastapi import HTTPException

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover - fallback for test environments
    def text(q):  # type: ignore
        return q

    Session = object

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Vacation Mode Service
# ------------------------------------------------------------

def enter_vacation_mode(db: Session, kingdom_id: int) -> datetime:
    """
    Enable Vacation Mode for a kingdom.

    Args:
        db: SQLAlchemy session
        kingdom_id: ID of the kingdom to mark as on vacation

    Returns:
        datetime: Timestamp when vacation mode will expire
    """
    expires = datetime.utcnow() + timedelta(days=7)

    try:
        db.execute(
            text(
                """
                UPDATE kingdoms
                SET is_on_vacation = TRUE,
                    vacation_started_at = NOW(),
                    vacation_expires_at = :exp
                WHERE kingdom_id = :kid
                """
            ),
            {"kid": kingdom_id, "exp": expires},
        )
        db.commit()
        logger.info("Kingdom %s entered Vacation Mode until %s", kingdom_id, expires)
        return expires

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to enter vacation mode for kingdom_id=%s", kingdom_id)
        raise HTTPException(status_code=500, detail="Failed to enter Vacation Mode.")


def exit_vacation_mode(db: Session, kingdom_id: int) -> None:
    """
    Disable Vacation Mode for a kingdom.

    Args:
        db: SQLAlchemy session
        kingdom_id: ID of the kingdom to exit vacation
    """
    try:
        db.execute(
            text(
                """
                UPDATE kingdoms
                SET is_on_vacation = FALSE,
                    vacation_started_at = NULL,
                    vacation_expires_at = NULL
                WHERE kingdom_id = :kid
                """
            ),
            {"kid": kingdom_id},
        )
        db.commit()
        logger.info("Kingdom %s exited Vacation Mode", kingdom_id)

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to exit vacation mode for kingdom_id=%s", kingdom_id)
        raise HTTPException(status_code=500, detail="Failed to exit Vacation Mode.")


def can_exit_vacation(db: Session, kingdom_id: int) -> bool:
    """
    Check whether a kingdom's vacation period has expired.

    Args:
        db: SQLAlchemy session
        kingdom_id: ID of the kingdom

    Returns:
        bool: True if vacation mode can be exited, else False
    """
    try:
        row = db.execute(
            text(
                "SELECT vacation_expires_at FROM kingdoms WHERE kingdom_id = :kid"
            ),
            {"kid": kingdom_id},
        ).fetchone()

        if not row:
            return False

        expires = row[0]
        return expires is None or datetime.utcnow() >= expires

    except SQLAlchemyError:
        logger.warning("Failed to check vacation expiration for kingdom_id=%s", kingdom_id)
        return False


def check_vacation_mode(db: Session, kingdom_id: int) -> None:
    """
    Raise an HTTP error if the kingdom is currently in Vacation Mode.

    Args:
        db: SQLAlchemy session
        kingdom_id: ID of the kingdom to check

    Raises:
        HTTPException: If the kingdom is currently marked as in Vacation Mode
    """
    try:
        row = db.execute(
            text("SELECT is_on_vacation FROM kingdoms WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()

        if row and row[0]:
            raise HTTPException(status_code=403, detail="Kingdom is in Vacation Mode.")

    except SQLAlchemyError:
        logger.warning("Vacation check failed for kingdom_id=%s", kingdom_id)
        raise HTTPException(status_code=500, detail="Vacation Mode check failed.")
