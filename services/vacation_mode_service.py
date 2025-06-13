# Project Name: Kingmakers Rise©
# File Name: vacation_mode_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from datetime import datetime, timedelta

from fastapi import HTTPException
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback for tests
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def enter_vacation_mode(db: Session, kingdom_id: int) -> datetime:
    """Mark the kingdom as in Vacation Mode and return the expiry."""
    expires = datetime.utcnow() + timedelta(days=7)
    db.execute(
        text(
            "UPDATE kingdoms SET is_on_vacation = TRUE, "
            "vacation_started_at = NOW(), vacation_expires_at = :exp "
            "WHERE kingdom_id = :kid"
        ),
        {"kid": kingdom_id, "exp": expires},
    )
    db.commit()
    return expires


def exit_vacation_mode(db: Session, kingdom_id: int) -> None:
    """Clear Vacation Mode flags for the kingdom."""
    db.execute(
        text(
            "UPDATE kingdoms SET is_on_vacation = FALSE, "
            "vacation_started_at = NULL, vacation_expires_at = NULL "
            "WHERE kingdom_id = :kid"
        ),
        {"kid": kingdom_id},
    )
    db.commit()


def can_exit_vacation(db: Session, kingdom_id: int) -> bool:
    """Return True if the kingdom can exit Vacation Mode."""
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


def check_vacation_mode(db: Session, kingdom_id: int) -> None:
    """Raise HTTPException if the kingdom is in Vacation Mode."""
    row = db.execute(
        text("SELECT is_on_vacation FROM kingdoms WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    if row and row[0]:
        raise HTTPException(status_code=403, detail="Kingdom is in Vacation Mode.")
