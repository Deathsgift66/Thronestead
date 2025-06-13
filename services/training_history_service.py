# Project Name: Kingmakers Rise©
# File Name: training_history_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def record_training(
    db: Session,
    kingdom_id: int,
    unit_id: int,
    unit_name: str,
    quantity: int,
    source: str,
    initiated_at: str,
    trained_by: str | None,
    xp_awarded: int,
    modifiers_applied: dict | None,
) -> int:
    """Insert a new training history row and return its id."""
    result = db.execute(
        text(
            """
            INSERT INTO training_history (
                kingdom_id, unit_id, unit_name, quantity, completed_at,
                source, initiated_at, trained_by, xp_awarded, modifiers_applied
            ) VALUES (
                :kid, :uid, :uname, :qty, now(),
                :src, :init, :tby, :xp, :mods
            ) RETURNING history_id
            """
        ),
        {
            "kid": kingdom_id,
            "uid": unit_id,
            "uname": unit_name,
            "qty": quantity,
            "src": source,
            "init": initiated_at,
            "tby": trained_by,
            "xp": xp_awarded,
            "mods": modifiers_applied or {},
        },
    )
    row = result.fetchone()
    db.commit()
    return row[0] if row else 0


def fetch_history(db: Session, kingdom_id: int, limit: int = 50) -> list[dict]:
    """Return recent training history for a kingdom."""
    rows = db.execute(
        text(
            """
            SELECT unit_name, quantity, completed_at, source, xp_awarded
            FROM training_history
            WHERE kingdom_id = :kid
            ORDER BY completed_at DESC
            LIMIT :lim
            """
        ),
        {"kid": kingdom_id, "lim": limit},
    ).fetchall()

    return [
        {
            "unit_name": r[0],
            "quantity": r[1],
            "completed_at": r[2],
            "source": r[3],
            "xp_awarded": r[4],
        }
        for r in rows
    ]
