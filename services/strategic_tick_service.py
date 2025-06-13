# Project Name: Kingmakers Rise©
# File Name: strategic_tick_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from __future__ import annotations

"""Automation helpers for periodic game state updates."""

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore

from services.kingdom_quest_service import expire_quests


def _log_unified(db: Session, event_type: str, details: str) -> None:
    """Write an entry to the unified logs table if available."""
    try:
        db.execute(
            text(
                "INSERT INTO unified_logs (event_type, details) "
                "VALUES (:et, :de)"
            ),
            {"et": event_type, "de": details},
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - ignore missing table
        logging.warning("Unified logs unavailable: %s", exc)


def _notify_event(db: Session, event_type: str, ref_id: int, info: str = "") -> None:
    """Insert an entry into event_notification_log if the table exists."""
    try:
        db.execute(
            text(
                "INSERT INTO event_notification_log (event_type, reference_id, info) "
                "VALUES (:et, :rid, :info)"
            ),
            {"et": event_type, "rid": ref_id, "info": info},
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - ignore missing table
        logging.warning("Event notification log unavailable: %s", exc)


def update_project_progress(db: Session) -> int:
    """Complete any alliance projects whose timer has elapsed."""
    result = db.execute(
        text(
            "UPDATE projects_alliance_in_progress "
            "SET status='completed', last_updated = now() "
            "WHERE status='building' AND expected_end <= now()"
        )
    )
    db.commit()
    count = getattr(result, "rowcount", 0)
    if count:
        _log_unified(db, "project_completed", f"{count} projects finished")
    return count


def update_quest_progress(db: Session) -> int:
    """Expire overdue quests and log newly completed ones."""
    completed = db.execute(
        text(
            "UPDATE quest_kingdom_tracking "
            "SET status='completed', last_updated = now() "
            "WHERE status='active' AND progress >= 100"
        )
    )
    expired = expire_quests(db)
    db.commit()
    done = getattr(completed, "rowcount", 0)
    if done:
        _log_unified(db, "quest_completed", f"{done} quests completed")
    total = done + expired
    return total


def expire_treaties(db: Session) -> int:
    """Expire alliance and kingdom treaties past their end date."""
    res_a = db.execute(
        text(
            "UPDATE alliance_treaties "
            "SET status='expired' "
            "WHERE status='active' AND expires_at IS NOT NULL AND expires_at < now()"
        )
    )
    res_k = db.execute(
        text(
            "UPDATE kingdom_treaties "
            "SET status='expired' "
            "WHERE status='active' AND expires_at IS NOT NULL AND expires_at < now()"
        )
    )
    db.commit()
    count = (getattr(res_a, "rowcount", 0) or 0) + (getattr(res_k, "rowcount", 0) or 0)
    if count:
        _log_unified(db, "treaties_expired", f"{count} treaties expired")
    return count


def activate_pending_wars(db: Session) -> int:
    """Activate wars scheduled to start and notify players."""
    rows = db.execute(
        text(
            "SELECT war_id FROM wars WHERE status='pending' AND start_date <= now()"
        )
    ).fetchall()
    war_ids = [r[0] for r in rows]
    if war_ids:
        db.execute(
            text(
                "UPDATE wars SET status='active' WHERE war_id = ANY(:ids)"
            ),
            {"ids": war_ids},
        )
    db.commit()
    for wid in war_ids:
        _notify_event(db, "new_war", wid)
    if war_ids:
        _log_unified(db, "wars_activated", f"{len(war_ids)} wars activated")
    return len(war_ids)


def check_war_status(db: Session) -> int:
    """Conclude wars that have passed their end date."""
    res_k = db.execute(
        text(
            "UPDATE wars SET status='concluded' "
            "WHERE status='active' AND end_date < now()"
        )
    )
    res_a = db.execute(
        text(
            "UPDATE alliance_wars SET war_status='concluded' "
            "WHERE war_status='active' AND end_date < now()"
        )
    )
    db.commit()
    count = (getattr(res_k, "rowcount", 0) or 0) + (getattr(res_a, "rowcount", 0) or 0)
    if count:
        _log_unified(db, "wars_concluded", f"{count} wars concluded")
    return count


def process_tick(db: Session) -> None:
    """Run all strategic backend maintenance tasks."""
    update_project_progress(db)
    update_quest_progress(db)
    expire_treaties(db)
    activate_pending_wars(db)
    check_war_status(db)
