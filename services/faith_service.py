# Project Name: Thronestead©
# File Name: faith_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
"""Utility functions for kingdom faith progression and blessings."""

from __future__ import annotations

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore
    SQLAlchemyError = Exception  # type: ignore

from .progression_service import _merge_modifiers, invalidate_cache

logger = logging.getLogger(__name__)

# Faith required per level
FAITH_PER_LEVEL = 100

# Simple demo blessing catalogue
BLESSINGS: dict[str, dict] = {
    "blessing_1": {
        "level": 2,
        "modifiers": {"production_bonus": {"faith_income": 1}},
    },
    "blessing_2": {
        "level": 3,
        "modifiers": {"combat_bonus": {"attack_bonus": 1}},
    },
    "blessing_3": {
        "level": 5,
        "modifiers": {"defense_bonus": {"castle_defense": 1}},
    },
}


def gain_faith(db: Session, kingdom_id: int, amount: int) -> None:
    """Increase faith points for a kingdom and handle level ups."""
    try:
        row = db.execute(
            text(
                "SELECT faith_points, faith_level FROM kingdom_religion "
                "WHERE kingdom_id = :kid"
            ),
            {"kid": kingdom_id},
        ).fetchone()
        if not row:
            points = 0
            level = 1
            db.execute(
                text(
                    "INSERT INTO kingdom_religion (kingdom_id, faith_points, faith_level) "
                    "VALUES (:kid, 0, 1) ON CONFLICT DO NOTHING"
                ),
                {"kid": kingdom_id},
            )
        else:
            points, level = row
        total = int(points or 0) + amount
        leveled = False
        while total >= level * FAITH_PER_LEVEL:
            total -= level * FAITH_PER_LEVEL
            level += 1
            leveled = True

        db.execute(
            text(
                "UPDATE kingdom_religion SET faith_points = :pts, faith_level = :lvl "
                "WHERE kingdom_id = :kid"
            ),
            {"pts": total, "lvl": level, "kid": kingdom_id},
        )
        if leveled:
            unlock_blessings(db, kingdom_id, level)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to gain faith for kingdom %s", kingdom_id)


def unlock_blessings(db: Session, kingdom_id: int, new_level: int) -> None:
    """Unlock blessings up to the new level for a kingdom."""
    try:
        row = db.execute(
            text(
                "SELECT blessings FROM kingdom_religion WHERE kingdom_id = :kid"
            ),
            {"kid": kingdom_id},
        ).fetchone()
        blessings = row[0] if row and row[0] else {}
        updated = False
        for code, info in BLESSINGS.items():
            if new_level >= info.get("level", 0) and code not in blessings:
                blessings[code] = True
                updated = True
        if updated:
            ordered = [b for b in BLESSINGS if b in blessings]
            db.execute(
                text(
                    """
                    UPDATE kingdom_religion
                       SET blessings = :b,
                           blessing_1 = :b1,
                           blessing_2 = :b2,
                           blessing_3 = :b3
                     WHERE kingdom_id = :kid
                    """
                ),
                {
                    "b": blessings,
                    "b1": ordered[0] if len(ordered) > 0 else None,
                    "b2": ordered[1] if len(ordered) > 1 else None,
                    "b3": ordered[2] if len(ordered) > 2 else None,
                    "kid": kingdom_id,
                },
            )
            db.commit()
            invalidate_cache(kingdom_id)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to unlock blessings for kingdom %s", kingdom_id)


def _get_faith_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return aggregated modifiers from active blessings."""
    try:
        row = db.execute(
            text("SELECT blessings FROM kingdom_religion WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
        active = row[0] if row and row[0] else {}
        mods: dict = {}
        for code in active:
            info = BLESSINGS.get(code)
            if info:
                _merge_modifiers(mods, info.get("modifiers", {}))
        return mods
    except SQLAlchemyError:
        logger.exception("Failed loading faith modifiers for %s", kingdom_id)
        return {}
