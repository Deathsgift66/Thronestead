# Project Name: Thronestead©
# File Name: faith_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Utility functions for kingdom faith progression and blessings."""

from __future__ import annotations

import logging

from services.sqlalchemy_support import Session, SQLAlchemyError, text

from services.modifiers_utils import _merge_modifiers, invalidate_cache

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
    """Unlock blessings up to ``new_level`` for ``kingdom_id``."""
    try:
        row = db.execute(
            text("SELECT blessings FROM kingdom_religion WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
        blessings = dict(row[0]) if row and row[0] else {}

        newly_unlocked = {
            code
            for code, info in BLESSINGS.items()
            if new_level >= info.get("level", 0) and code not in blessings
        }
        if not newly_unlocked:
            return

        blessings.update({code: True for code in newly_unlocked})
        ordered = [code for code in BLESSINGS if blessings.get(code)]
        b1, b2, b3 = (ordered + [None, None, None])[:3]

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
            {"b": blessings, "b1": b1, "b2": b2, "b3": b3, "kid": kingdom_id},
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
