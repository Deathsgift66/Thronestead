# Project Name: Thronestead©
# File Name: training_history_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Handles tracking of completed troop training records.

from __future__ import annotations

import logging
from typing import Optional

from .unit_xp_service import award_unit_xp

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
    speed_modifier: float = 1.0,
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
        xp_per_unit: XP each unit grants before modifiers
        speed_modifier: Multiplier applied to XP reward

    Returns:
        int: ID of the new training_history row
    """
    try:
        xp_awarded = int(xp_per_unit * quantity * speed_modifier)

        result = db.execute(
            text(
                """
                INSERT INTO training_history (
                    kingdom_id, unit_id, unit_name, quantity, completed_at,
                    source, initiated_at, trained_by, xp_awarded,
                    modifiers_applied, speed_modifier
                ) VALUES (
                    :kid, :uid, :uname, :qty, now(),
                    :src, :init, :tby, :xp,
                    :mods, :speed
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
                "xp": xp_awarded,
                "mods": modifiers_applied or {},
                "speed": speed_modifier,
            },
        )
        row = result.fetchone()

        award_unit_xp(db, kingdom_id, unit_name, xp_awarded, quantity)

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
