from __future__ import annotations

"""Utility functions for periodic maintenance tasks."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from services.resource_service import ensure_kingdom_resource_row


def verify_kingdom_resources(db: Session) -> int:
    """Ensure every kingdom has a resources row."""
    rows = db.execute(text("SELECT kingdom_id FROM kingdoms")).fetchall()
    for (kid,) in rows:
        ensure_kingdom_resource_row(db, kid)
    db.commit()
    return len(rows)


def cleanup_zombie_training_queue(db: Session) -> int:
    """Remove stale training orders past their end time."""
    result = db.execute(
        text(
            "DELETE FROM training_queue "
            "WHERE status IN ('queued', 'training') "
            "AND training_ends_at < now()"
        )
    )
    db.commit()
    return getattr(result, "rowcount", 0)


def cleanup_zombie_spy_missions(db: Session) -> int:
    """Fail any spy missions stuck in active state past an hour."""
    result = db.execute(
        text(
            "UPDATE spy_missions "
            "SET status = 'fail' "
            "WHERE status = 'active' "
            "AND completed_at < now() - interval '1 hour'"
        )
    )
    db.commit()
    return getattr(result, "rowcount", 0)
