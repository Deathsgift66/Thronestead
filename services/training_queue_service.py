# Project Name: Kingmakers Rise©
# File Name: training_queue_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def add_training_order(
    db: Session,
    kingdom_id: int,
    unit_id: int,
    unit_name: str,
    quantity: int,
    base_training_seconds: int,
    training_speed_modifier: float = 1.0,
    xp_per_unit: int = 0,
    modifiers_applied: dict | None = None,
    initiated_by: str | None = None,
    priority: int = 1,
) -> int:
    """Insert a new row into training_queue and return the queue_id."""
    result = db.execute(
        text(
            """
            INSERT INTO training_queue (
                kingdom_id, unit_id, unit_name, quantity,
                training_ends_at, started_at, status,
                training_speed_modifier, xp_per_unit, modifiers_applied,
                initiated_by, priority
            ) VALUES (
                :kid, :uid, :uname, :qty,
                now() + (:base * :speed) * interval '1 second', now(), 'queued',
                :speed, :xp, :mods,
                :init, :pri
            ) RETURNING queue_id
            """
        ),
        {
            "kid": kingdom_id,
            "uid": unit_id,
            "uname": unit_name,
            "qty": quantity,
            "base": base_training_seconds,
            "speed": training_speed_modifier,
            "xp": xp_per_unit,
            "mods": modifiers_applied or {},
            "init": initiated_by,
            "pri": priority,
        },
    )
    row = result.fetchone()
    db.commit()
    return row[0] if row else 0


def fetch_queue(db: Session, kingdom_id: int) -> list[dict]:
    """Return active training orders for a kingdom ordered by priority."""
    rows = db.execute(
        text(
            """
            SELECT queue_id, unit_name, quantity, training_ends_at, status
            FROM training_queue
            WHERE kingdom_id = :kid
              AND status IN ('queued', 'training')
            ORDER BY priority DESC, started_at ASC
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
        }
        for r in rows
    ]


def cancel_training(db: Session, queue_id: int, kingdom_id: int) -> None:
    """Cancel a training order for a kingdom."""
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


def mark_completed(db: Session, queue_id: int) -> None:
    """Mark a training order as completed."""
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
