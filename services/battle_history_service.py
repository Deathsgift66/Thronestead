# Project Name: Thronestead©
# File Name: battle_history_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Service for retrieving concluded battle history records."""

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

logger = logging.getLogger(__name__)


def fetch_history(db: Session, kingdom_id: int, limit: int = 25) -> list[dict]:
    """Return recent completed wars involving ``kingdom_id``."""
    try:
        rows = db.execute(
            text(
                """
                SELECT war_id, attacker_name, defender_name, outcome,
                       attacker_score, defender_score, end_date
                FROM wars
                WHERE (attacker_kingdom_id = :kid OR defender_kingdom_id = :kid)
                  AND status = 'ended'
                ORDER BY end_date DESC
                LIMIT :lim
                """
            ),
            {"kid": kingdom_id, "lim": limit},
        ).fetchall()

        return [
            {
                "war_id": r[0],
                "attacker_name": r[1],
                "defender_name": r[2],
                "outcome": r[3],
                "attacker_score": r[4],
                "defender_score": r[5],
                "end_date": r[6],
            }
            for r in rows
        ]
    except SQLAlchemyError:
        logger.warning("Failed to fetch battle history for kingdom %s", kingdom_id)
        return []
