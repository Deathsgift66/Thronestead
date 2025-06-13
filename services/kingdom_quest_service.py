"""Service functions for kingdom quest tracking."""

from datetime import datetime, timedelta
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def start_quest(db: Session, kingdom_id: int, quest_code: str, started_by: str) -> datetime:
    """Insert or reset a kingdom quest row and return the ends_at timestamp."""
    duration_row = db.execute(
        text("SELECT duration_hours FROM quest_kingdom_catalogue WHERE quest_code = :code"),
        {"code": quest_code},
    ).fetchone()
    if not duration_row:
        raise ValueError("Quest not found")

    duration_hours = duration_row[0] or 0
    ends_at = datetime.utcnow() + timedelta(hours=duration_hours)

    db.execute(
        text(
            """
            INSERT INTO quest_kingdom_tracking (
                kingdom_id, quest_code, status, progress, progress_details,
                ends_at, started_by, attempt_count
            ) VALUES (:kid, :code, 'active', 0, '{}'::jsonb, :end, :uid, 1)
            ON CONFLICT (kingdom_id, quest_code)
            DO UPDATE SET
                status = 'active',
                progress = 0,
                progress_details = '{}'::jsonb,
                ends_at = EXCLUDED.ends_at,
                started_by = EXCLUDED.started_by,
                attempt_count = quest_kingdom_tracking.attempt_count + 1,
                started_at = now(),
                last_updated = now()
            """
        ),
        {"kid": kingdom_id, "code": quest_code, "end": ends_at, "uid": started_by},
    )
    db.commit()
    return ends_at


def update_progress(db: Session, kingdom_id: int, quest_code: str, progress: int, details: dict) -> None:
    """Update progress fields for a quest."""
    db.execute(
        text(
            """
            UPDATE quest_kingdom_tracking
               SET progress = :prog,
                   progress_details = :details,
                   last_updated = now()
             WHERE kingdom_id = :kid AND quest_code = :code
            """
        ),
        {"kid": kingdom_id, "code": quest_code, "prog": progress, "details": details},
    )
    db.commit()


def complete_quest(db: Session, kingdom_id: int, quest_code: str) -> None:
    """Mark a quest as completed."""
    db.execute(
        text(
            "UPDATE quest_kingdom_tracking SET status='completed', last_updated = now() "
            "WHERE kingdom_id = :kid AND quest_code = :code"
        ),
        {"kid": kingdom_id, "code": quest_code},
    )
    db.commit()


def cancel_quest(db: Session, kingdom_id: int, quest_code: str) -> None:
    """Mark a quest as cancelled."""
    db.execute(
        text(
            "UPDATE quest_kingdom_tracking SET status='cancelled', last_updated = now() "
            "WHERE kingdom_id = :kid AND quest_code = :code"
        ),
        {"kid": kingdom_id, "code": quest_code},
    )
    db.commit()


def expire_quests(db: Session) -> int:
    """Mark overdue active quests as expired and return count."""
    result = db.execute(
        text(
            "UPDATE quest_kingdom_tracking "
            "SET status='expired', last_updated = now() "
            "WHERE status='active' AND ends_at < now()"
        )
    )
    db.commit()
    return getattr(result, "rowcount", 0)
