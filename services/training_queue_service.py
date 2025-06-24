# Project Name: Thronestead©
# File Name: training_queue_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Handles adding, updating, and viewing training queue entries for troops.

from __future__ import annotations

import logging
from typing import Optional

try:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Training Queue Service Functions
# ------------------------------------------------------------


def add_training_order(
    db: Session,
    kingdom_id: int,
    unit_id: int,
    unit_name: str,
    quantity: int,
    base_training_seconds: int,
    training_speed_modifier: float = 1.0,
    modifiers_applied: Optional[dict] = None,
    initiated_by: Optional[str] = None,
    priority: int = 1,
) -> int:
    """
    Add a new training job to the queue.

    Args:
        db: DB session
        kingdom_id: ID of the training kingdom
        unit_id: ID of the unit being trained
        unit_name: Display name
        quantity: Quantity of units to train
        base_training_seconds: Base time in seconds
        training_speed_modifier: Multiplier (e.g., 0.8 = 20% faster)
        modifiers_applied: Modifier details for tracking
        initiated_by: User ID
        priority: Queue priority (higher = earlier)

    Returns:
        int: ID of the newly inserted training queue entry
    """
    try:
        result = db.execute(
            text(
                """
                INSERT INTO training_queue (
                    kingdom_id, unit_id, unit_name, quantity,
                    training_ends_at, started_at, status,
                    training_speed_modifier, modifiers_applied,
                    initiated_by, priority
                ) VALUES (
                    :kid, :uid, :uname, :qty,
                    now() + (:base * :speed) * interval '1 second', now(), 'queued',
                    :speed, :mods,
                    :init, :pri
                )
                RETURNING queue_id
                """
            ),
            {
                "kid": kingdom_id,
                "uid": unit_id,
                "uname": unit_name,
                "qty": quantity,
                "base": base_training_seconds,
                "speed": training_speed_modifier,
                "mods": modifiers_applied or {},
                "init": initiated_by,
                "pri": priority,
            },
        )
        row = result.fetchone()
        db.commit()
        return int(row[0]) if row else 0

    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to insert training queue entry for %s x%d", unit_name, quantity
        )
        return 0


def fetch_queue(db: Session, kingdom_id: int) -> list[dict]:
    """
    Fetch all active queue entries for a kingdom, ordered by priority and start time.

    Args:
        db: DB session
        kingdom_id: Kingdom whose queue is being requested

    Returns:
        List[dict]: List of queued or in-progress units
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT q.queue_id, q.unit_name, q.quantity, q.training_ends_at, q.status,
                       COALESCE(us.is_support, false) AS is_support,
                       COALESCE(us.is_siege, false) AS is_siege
                FROM training_queue q
                LEFT JOIN unit_stats us ON q.unit_name = us.unit_type
                WHERE q.kingdom_id = :kid
                  AND q.status IN ('queued', 'training')
                ORDER BY q.priority DESC, q.started_at ASC
                """
            ),
            {"kid": kingdom_id},
        ).fetchall()

        return [
            {
                "queue_id": r[0],
                "unit_name": r[1],
                "quantity": r[2],
                "training_ends_at": r[3],
                "status": r[4],
                "is_support": r[5],
                "is_siege": r[6],
            }
            for r in rows
        ]
    except SQLAlchemyError:
        logger.warning("Unable to fetch training queue for kingdom_id=%s", kingdom_id)
        return []


def cancel_training(db: Session, queue_id: int, kingdom_id: int) -> None:
    """
    Cancel a training order.

    Args:
        db: DB session
        queue_id: ID of the training queue row
        kingdom_id: Owner kingdom for validation
    """
    try:
        db.execute(
            text(
                """
                UPDATE training_queue
                SET status = 'cancelled', last_updated = now()
                WHERE queue_id = :qid AND kingdom_id = :kid
                """
            ),
            {"qid": queue_id, "kid": kingdom_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to cancel training for queue_id=%s", queue_id)


def mark_completed(db: Session, queue_id: int) -> None:
    """
    Mark a training entry as completed.

    Args:
        db: DB session
        queue_id: ID of the queue row to complete
    """
    try:
        db.execute(
            text(
                """
                UPDATE training_queue
                SET status = 'completed', last_updated = now()
                WHERE queue_id = :qid
                """
            ),
            {"qid": queue_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to mark queue_id=%s as completed", queue_id)
