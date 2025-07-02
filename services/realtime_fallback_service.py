from __future__ import annotations

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - SQLAlchemy optional

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

from services import training_queue_service

logger = logging.getLogger(__name__)

_DEFAULT_TRAINING_GAP = 3600  # 1 hour
_DEFAULT_MOVEMENT_STALE = 900  # 15 minutes


def finalize_overdue_training(db: Session) -> int:
    """Auto-complete training orders past their end time."""
    return training_queue_service.finalize_completed_orders(db)


def fallback_on_idle_training(db: Session, gap_seconds: int = _DEFAULT_TRAINING_GAP) -> int:
    """Mark stale training orders as completed."""
    result = db.execute(
        text(
            """
            UPDATE training_queue
               SET status = 'completed', last_updated = now()
             WHERE status IN ('queued', 'training')
               AND now() - started_at > :gap * interval '1 second'
               AND now() - last_updated > :gap * interval '1 second'
            """
        ),
        {"gap": gap_seconds},
    )
    db.commit()
    return getattr(result, "rowcount", 0)


def mark_stale_engaged_units_defeated(db: Session, stale_seconds: int = _DEFAULT_MOVEMENT_STALE) -> int:
    """Auto-mark engaged units as defeated after inactivity."""
    result = db.execute(
        text(
            """
            UPDATE unit_movements
               SET status = 'defeated', last_updated = now()
             WHERE status = 'engaged'
               AND last_updated < now() - :secs * interval '1 second'
            """
        ),
        {"secs": stale_seconds},
    )
    db.commit()
    return getattr(result, "rowcount", 0)
