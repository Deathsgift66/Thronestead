# Project Name: Thronestead©
# File Name: alliance_achievement_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Service functions for alliance achievements."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Award Achievement
# ----------------------------------------------------------------------------

def award_achievement(
    db: Session, alliance_id: int, achievement_code: str
) -> Optional[int]:
    """Award an achievement to an alliance if not already earned.

    Returns the points reward if newly awarded, otherwise ``None``.
    """
    exists = db.execute(
        text(
            "SELECT 1 FROM alliance_achievements "
            "WHERE alliance_id = :aid AND achievement_code = :code"
        ),
        {"aid": alliance_id, "code": achievement_code},
    ).fetchone()

    if exists:
        return None

    db.execute(
        text(
            "INSERT INTO alliance_achievements (alliance_id, achievement_code) "
            "VALUES (:aid, :code)"
        ),
        {"aid": alliance_id, "code": achievement_code},
    )

    points = db.execute(
        text(
            "SELECT points_reward FROM alliance_achievement_catalogue "
            "WHERE achievement_code = :code"
        ),
        {"code": achievement_code},
    ).scalar()

    db.commit()
    return int(points) if points is not None else 0


# ----------------------------------------------------------------------------
# List Achievements
# ----------------------------------------------------------------------------

def list_achievements(db: Session, alliance_id: int) -> list[dict]:
    """Return all achievements and unlock status for an alliance."""
    rows = db.execute(
        text(
            """
            SELECT c.achievement_code, c.name, c.description, c.category,
                   c.points_reward, c.icon_url, c.is_hidden, c.is_seasonal,
                   a.awarded_at
              FROM alliance_achievement_catalogue c
         LEFT JOIN alliance_achievements a
                ON c.achievement_code = a.achievement_code
               AND a.alliance_id = :aid
             ORDER BY c.category, c.achievement_code
            """
        ),
        {"aid": alliance_id},
    ).fetchall()

    achievements: list[dict] = []
    for r in rows:
        if r[6] and r[8] is None:
            continue
        achievements.append(
            {
                "achievement_code": r[0],
                "name": r[1],
                "description": r[2],
                "category": r[3],
                "points_reward": r[4],
                "icon_url": r[5],
                "is_hidden": r[6],
                "is_seasonal": r[7],
                "awarded_at": r[8],
            }
        )
    return achievements
