# Project Name: Thronestead©
# File Name: unit_xp_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Centralized utilities for applying unit experience and handling level ups."""

from __future__ import annotations

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

logger = logging.getLogger(__name__)

XP_PER_LEVEL = 100


def award_unit_xp(
    db: Session, kingdom_id: int, unit_type: str, xp: int, quantity: int = 0
) -> None:
    """Add XP (and optional quantity) to a unit stack.

    This will insert a new level 1 stack if none exists.
    """
    db.execute(
        text(
            """
            INSERT INTO kingdom_troops (kingdom_id, unit_type, unit_level, quantity, unit_xp)
            VALUES (:kid, :ut, 1, :qty, :xp)
            ON CONFLICT (kingdom_id, unit_type, unit_level)
            DO UPDATE SET
                quantity = kingdom_troops.quantity + :qty,
                unit_xp = kingdom_troops.unit_xp + :xp
            """
        ),
        {"kid": kingdom_id, "ut": unit_type, "qty": quantity, "xp": xp},
    )
    level_up_units(db, kingdom_id, unit_type)


def level_up_units(db: Session, kingdom_id: int, unit_type: str) -> None:
    """Convert accumulated XP into higher level troops."""
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


