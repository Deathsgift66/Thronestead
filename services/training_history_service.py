# Project Name: Thronestead©
# File Name: training_history_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Handles tracking of completed troop training records.

from __future__ import annotations

import logging
from typing import Optional

XP_PER_LEVEL = 100

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
# Training History Services
# ------------------------------------------------------------


def _add_unit_xp(
    db: Session,
    kingdom_id: int,
    unit_type: str,
    quantity: int,
    xp_per_unit: int,
) -> None:
    """Increase XP on the kingdom_troops row for this unit."""
    xp = xp_per_unit * quantity
    db.execute(
        text(
            """
            INSERT INTO kingdom_troops (kingdom_id, unit_type, unit_level, quantity, unit_xp)
            VALUES (:kid, :unit, 1, :qty, :xp)
            ON CONFLICT (kingdom_id, unit_type, unit_level)
            DO UPDATE SET quantity = kingdom_troops.quantity + :qty,
                          unit_xp = kingdom_troops.unit_xp + :xp
            """
        ),
        {"kid": kingdom_id, "unit": unit_type, "qty": quantity, "xp": xp},
    )


def level_up_units(db: Session, kingdom_id: int, unit_type: str) -> None:
    """Convert accumulated XP into unit levels."""
    row = db.execute(
        text(
            "SELECT quantity, unit_xp, unit_level FROM kingdom_troops "
            "WHERE kingdom_id = :kid AND unit_type = :unit "
            "ORDER BY unit_level ASC LIMIT 1"
        ),
        {"kid": kingdom_id, "unit": unit_type},
    ).fetchone()

    if not row:
        return

    qty, xp, level = row
    if xp < XP_PER_LEVEL:
        return

    levels = xp // XP_PER_LEVEL
    new_level = level + levels
    remaining = xp % XP_PER_LEVEL

    db.execute(
        text(
            "UPDATE kingdom_troops SET quantity = 0, unit_xp = :xp "
            "WHERE kingdom_id = :kid AND unit_type = :unit AND unit_level = :lvl"
        ),
        {"xp": remaining, "kid": kingdom_id, "unit": unit_type, "lvl": level},
    )

    db.execute(
        text(
            """
            INSERT INTO kingdom_troops (kingdom_id, unit_type, unit_level, quantity)
            VALUES (:kid, :unit, :lvl, :qty)
            ON CONFLICT (kingdom_id, unit_type, unit_level)
            DO UPDATE SET quantity = kingdom_troops.quantity + EXCLUDED.quantity
            """
        ),
        {"kid": kingdom_id, "unit": unit_type, "lvl": new_level, "qty": qty},
    )


def record_training(
    db: Session,
    kingdom_id: int,
    unit_id: int,
    unit_name: str,
    quantity: int,
    source: str,
    initiated_at: str,
    trained_by: Optional[str],
    modifiers_applied: Optional[dict],
    xp_per_unit: int = 0,
) -> int:
    """
    Record a completed unit training session.

    Args:
        db: Database session
        kingdom_id: Kingdom ID that trained the unit
        unit_id: Internal unit ID
        unit_name: Display name of the unit
        quantity: Number of units trained
        source: Source of training (e.g., 'training_queue')
        initiated_at: Timestamp when training started
        trained_by: User ID who initiated the training (if available)
        modifiers_applied: Dictionary of production modifiers applied

    Returns:
        int: ID of the new training_history row
    """
    try:
        result = db.execute(
            text(
                """
                INSERT INTO training_history (
                    kingdom_id, unit_id, unit_name, quantity, completed_at,
                    source, initiated_at, trained_by, modifiers_applied
                ) VALUES (
                    :kid, :uid, :uname, :qty, now(),
                    :src, :init, :tby, :mods
                )
                RETURNING history_id
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
                "mods": modifiers_applied or {},
            },
        )
        row = result.fetchone()

        _add_unit_xp(db, kingdom_id, unit_name, quantity, xp_per_unit)
        level_up_units(db, kingdom_id, unit_name)

        db.commit()
        return int(row[0]) if row else 0

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to record training session for unit %s", unit_name)
        return 0


def fetch_history(db: Session, kingdom_id: int, limit: int = 50) -> list[dict]:
    """
    Fetch the most recent unit training records for a given kingdom.

    Args:
        db: DB session
        kingdom_id: Kingdom to fetch records for
        limit: Max rows to return (default = 50)

    Returns:
        List[dict]: Recent training records
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT unit_name, quantity, completed_at, source
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
            }
            for r in rows
        ]

    except SQLAlchemyError:
        logger.warning("Failed to fetch training history for kingdom_id=%s", kingdom_id)
        return []
