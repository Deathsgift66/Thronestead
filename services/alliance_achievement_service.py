# Project Name: Thronestead©
# File Name: alliance_achievement_service.py
# Description: Manage alliance achievement unlocking and retrieval.

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def award_achievement(db: Session, alliance_id: int, achievement_code: str) -> Optional[int]:
    """Award an achievement to an alliance if not already earned.

    Returns the points reward if awarded, or ``None`` if already earned or on error.
    """
    try:
        # Check if the alliance already has this achievement
        row = db.execute(
            text(
                "SELECT 1 FROM alliance_achievements "
                "WHERE alliance_id = :aid AND achievement_code = :code"
            ),
            {"aid": alliance_id, "code": achievement_code},
        ).fetchone()
        if row:
            return None

        # Insert new achievement record
        db.execute(
            text(
                "INSERT INTO alliance_achievements (alliance_id, achievement_code) "
                "VALUES (:aid, :code)"
            ),
            {"aid": alliance_id, "code": achievement_code},
        )

        # Fetch points reward metadata
        reward_row = db.execute(
            text(
                "SELECT points_reward FROM alliance_achievement_catalogue "
                "WHERE achievement_code = :code"
            ),
            {"code": achievement_code},
        ).fetchone()
        points = reward_row[0] if reward_row else 0

        db.commit()
        return points
    except SQLAlchemyError:
        logger.exception("Failed to award alliance achievement %s", achievement_code)
        db.rollback()
        return None


def list_achievements(db: Session, alliance_id: int) -> list[dict]:
    """Return all alliance achievements with unlock status."""
    try:
        rows = db.execute(
            text(
                """
                SELECT c.achievement_code, c.name, c.description, c.category,
                       c.points_reward, c.badge_icon_url, c.is_hidden,
                       c.is_repeatable, a.awarded_at
                  FROM alliance_achievement_catalogue c
             LEFT JOIN alliance_achievements a
                    ON c.achievement_code = a.achievement_code
                   AND a.alliance_id = :aid
              ORDER BY c.category, c.achievement_code
                """
            ),
            {"aid": alliance_id},
        ).fetchall()

        achievements = []
        for r in rows:
            # Skip hidden achievements that are not unlocked
            if r[6] and r[8] is None:
                continue
            achievements.append(
                {
                    "achievement_code": r[0],
                    "name": r[1],
                    "description": r[2],
                    "category": r[3],
                    "points_reward": r[4],
                    "badge_icon_url": r[5],
                    "is_hidden": r[6],
                    "is_repeatable": r[7],
                    "awarded_at": r[8],
                }
            )
        return achievements
    except SQLAlchemyError:
        logger.exception("Failed to list achievements for alliance %d", alliance_id)
        return []
