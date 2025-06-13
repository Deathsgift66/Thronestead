# Project Name: Kingmakers Rise©
# File Name: research_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from __future__ import annotations

"""Service functions for kingdom technology research tracking."""

from datetime import datetime, timedelta
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def start_research(db: Session, kingdom_id: int, tech_code: str) -> datetime:
    """Begin research on a technology for the given kingdom.

    The function looks up the tech duration and inserts/updates the
    ``kingdom_research_tracking`` table with status ``active``.
    Returns the ``ends_at`` timestamp for convenience.
    """
    duration_row = db.execute(
        text(
            "SELECT duration_hours, prerequisites FROM tech_catalogue "
            "WHERE tech_code = :code AND is_active = true"
        ),
        {"code": tech_code},
    ).fetchone()
    if not duration_row:
        raise ValueError("Tech not found")

    duration_hours, prereqs = duration_row
    prereqs = prereqs or []

    if prereqs:
        rows = db.execute(
            text(
                "SELECT tech_code FROM kingdom_research_tracking "
                "WHERE kingdom_id = :kid AND status = 'completed'"
            ),
            {"kid": kingdom_id},
        ).fetchall()
        completed = {r[0] for r in rows}
        if not set(prereqs).issubset(completed):
            raise ValueError("Missing prerequisites")

    duration_hours = duration_hours or 0
    ends_at = datetime.utcnow() + timedelta(hours=duration_hours)

    db.execute(
        text(
            """
            INSERT INTO kingdom_research_tracking (
                kingdom_id, tech_code, status, progress, ends_at
            ) VALUES (:kid, :code, 'active', 0, :end)
            ON CONFLICT (kingdom_id, tech_code)
            DO UPDATE SET status='active', progress=0, ends_at=EXCLUDED.ends_at
            """
        ),
        {"kid": kingdom_id, "code": tech_code, "end": ends_at},
    )
    db.commit()
    return ends_at


def complete_finished_research(db: Session, kingdom_id: int) -> None:
    """Mark any finished research for the kingdom as completed."""
    db.execute(
        text(
            """
            UPDATE kingdom_research_tracking
               SET status='completed', progress=100
             WHERE kingdom_id = :kid
               AND status = 'active'
               AND ends_at <= NOW()
            """
        ),
        {"kid": kingdom_id},
    )
    db.commit()


def list_research(db: Session, kingdom_id: int) -> list[dict]:
    """Return research tracking rows for the kingdom."""
    rows = db.execute(
        text(
            """
            SELECT tech_code, status, progress, ends_at
              FROM kingdom_research_tracking
             WHERE kingdom_id = :kid
             ORDER BY tech_code
            """
        ),
        {"kid": kingdom_id},
    ).fetchall()

    return [
        {"tech_code": r[0], "status": r[1], "progress": r[2], "ends_at": r[3]}
        for r in rows
    ]


def is_tech_completed(db: Session, kingdom_id: int, tech_code: str) -> bool:
    """Return ``True`` if the kingdom has completed the given tech."""
    row = db.execute(
        text(
            """
            SELECT 1 FROM kingdom_research_tracking
             WHERE kingdom_id = :kid
               AND tech_code = :code
               AND status = 'completed'
            """
        ),
        {"kid": kingdom_id, "code": tech_code},
    ).fetchone()
    return row is not None
