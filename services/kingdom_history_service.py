# Comment
# Project Name: Thronestead©
# File Name: kingdom_history_service.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
# Description: Tracks kingdom history logs and aggregates comprehensive event timelines.

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ----------------------------------
# 🔹 Kingdom History Logging
# ----------------------------------


def log_event(
    db: Session, kingdom_id: int, event_type: str, event_details: str
) -> None:
    """
    Insert a new event into the kingdom's history log.
    """
    try:
        db.execute(
            text(
                """
                INSERT INTO kingdom_history_log (kingdom_id, event_type, event_details)
                VALUES (:kid, :etype, :details)
            """
            ),
            {"kid": kingdom_id, "etype": event_type, "details": event_details},
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to log event for kingdom %d", kingdom_id)
        raise RuntimeError("Failed to log kingdom event") from exc


def fetch_history(db: Session, kingdom_id: int, limit: int = 50) -> list[dict]:
    """
    Fetch recent history events for a kingdom, sorted by most recent first.

    Returns:
        List of dicts with: log_id, event_type, event_details, event_date
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT log_id, event_type, event_details, event_date
                FROM kingdom_history_log
                WHERE kingdom_id = :kid
                ORDER BY event_date DESC
                LIMIT :limit
            """
            ),
            {"kid": kingdom_id, "limit": limit},
        ).fetchall()

        return [
            {
                "log_id": r[0],
                "event_type": r[1],
                "event_details": r[2],
                "event_date": r[3],
            }
            for r in rows
        ]
    except SQLAlchemyError:
        logger.exception("Failed to fetch history for kingdom %d", kingdom_id)
        return []


# ----------------------------------
# 🔹 Aggregated Kingdom History View
# ----------------------------------


def fetch_full_history(db: Session, kingdom_id: int) -> dict:
    """
    Aggregates all major historical and progress logs tied to a kingdom.

    Returns:
        Dictionary with keys: core, timeline, wars_fought, achievements, titles,
        research_log, quests_log, training_log, projects_log
    """

    def single(query: str) -> dict:
        try:
            row = db.execute(text(query), {"kid": kingdom_id}).mappings().fetchone()
            return dict(row) if row else {}
        except SQLAlchemyError:
            logger.warning("Failed to fetch single row: %s", query)
            return {}

    def many(query: str) -> list[dict]:
        try:
            rows = db.execute(text(query), {"kid": kingdom_id}).mappings().fetchall()
            return [dict(r) for r in rows]
        except SQLAlchemyError:
            logger.warning("Failed to fetch many rows: %s", query)
            return []

    return {
        "core": single(
            """
            SELECT kingdom_name, ruler_name, created_at, motto, region
            FROM kingdoms WHERE kingdom_id = :kid
        """
        ),
        "timeline": many(
            """
            SELECT event_type, event_details, event_date
            FROM kingdom_history_log
            WHERE kingdom_id = :kid
            ORDER BY event_date DESC
        """
        ),
        "wars_fought": many(
            """
            SELECT war_id, attacker_id, defender_id, war_reason, outcome,
                   start_date, end_date
              FROM wars
             WHERE attacker_kingdom_id = :kid OR defender_kingdom_id = :kid
             ORDER BY start_date DESC
        """
        ),
        "achievements": many(
            """
            SELECT k.achievement_code, c.name, c.description, k.awarded_at
              FROM kingdom_achievements k
              JOIN kingdom_achievement_catalogue c
                ON k.achievement_code = c.achievement_code
             WHERE k.kingdom_id = :kid
        """
        ),
        "titles": many(
            """
            SELECT title, awarded_at
              FROM kingdom_titles
             WHERE kingdom_id = :kid
             ORDER BY awarded_at DESC
        """
        ),
        "research_log": many(
            """
            SELECT tech_code, status, progress, ends_at
              FROM kingdom_research_tracking
             WHERE kingdom_id = :kid
        """
        ),
        "quests_log": many(
            """
            SELECT quest_code, status, started_at, ends_at
              FROM quest_kingdom_tracking
             WHERE kingdom_id = :kid
             ORDER BY started_at DESC
        """
        ),
        "training_log": many(
            """
            SELECT unit_name, quantity, completed_at
              FROM training_history
             WHERE kingdom_id = :kid
             ORDER BY completed_at DESC
        """
        ),
        "projects_log": many(
            """
            SELECT p.project_code, c.name, p.starts_at, p.ends_at
              FROM projects_player p
              JOIN project_player_catalogue c ON p.project_code = c.project_code
             WHERE p.kingdom_id = :kid
             ORDER BY p.starts_at DESC
        """
        ),
    }
