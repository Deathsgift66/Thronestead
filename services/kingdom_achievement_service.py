# Project Name: Thronestead©
# File Name: kingdom_achievement_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Handles unlocking, retrieving, and rewarding achievements for kingdoms.

import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ----------------------------
# Award Achievement
# ----------------------------

def award_achievement(db: Session, kingdom_id: int, achievement_code: str) -> Optional[dict]:
    """
    Awards an achievement to the kingdom if not already earned.

    Returns:
        dict: Reward JSON if newly awarded.
        None: If already awarded or an error occurs.
    """
    try:
        # Check for existing award
        exists = db.execute(
            text("""
                SELECT 1 FROM kingdom_achievements
                 WHERE kingdom_id = :kid AND achievement_code = :code
            """),
            {"kid": kingdom_id, "code": achievement_code},
        ).fetchone()

        if exists:
            return None  # Already earned

        # Insert achievement
        db.execute(
            text("""
                INSERT INTO kingdom_achievements (kingdom_id, achievement_code)
                VALUES (:kid, :code)
            """),
            {"kid": kingdom_id, "code": achievement_code},
        )

        # Fetch reward metadata
        reward_row = db.execute(
            text("""
                SELECT reward FROM kingdom_achievement_catalogue
                 WHERE achievement_code = :code
            """),
            {"code": achievement_code},
        ).fetchone()

        db.commit()
        return reward_row[0] if reward_row else None

    except SQLAlchemyError:
        logger.exception("Failed to award achievement %s", achievement_code)
        db.rollback()
        return None

# ----------------------------
# List Achievements
# ----------------------------

def list_achievements(db: Session, kingdom_id: int) -> list[dict]:
    """
    Returns all available achievements and unlock status for the given kingdom.

    Hidden achievements that have not been unlocked are omitted.

    Returns:
        list of dicts with keys:
            achievement_code, name, description, category, reward, points, is_hidden, awarded_at
    """
    try:
        rows = db.execute(
            text("""
                SELECT c.achievement_code, c.name, c.description, c.category,
                       c.reward, c.points, c.is_hidden, a.awarded_at
                  FROM kingdom_achievement_catalogue c
             LEFT JOIN kingdom_achievements a
                    ON c.achievement_code = a.achievement_code
                   AND a.kingdom_id = :kid
              ORDER BY c.category, c.achievement_code
            """),
            {"kid": kingdom_id},
        ).fetchall()

        achievements = []
        for r in rows:
            # r[6] = is_hidden, r[7] = awarded_at
            if r[6] and r[7] is None:
                continue  # Skip hidden & locked
            achievements.append({
                "achievement_code": r[0],
                "name": r[1],
                "description": r[2],
                "category": r[3],
                "reward": r[4],
                "points": r[5],
                "is_hidden": r[6],
                "awarded_at": r[7],
            })

        return achievements

    except SQLAlchemyError:
        logger.exception("Failed to list achievements for kingdom %d", kingdom_id)
        return []
