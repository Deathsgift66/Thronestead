# Project Name: Thronestead©
# File Name: kingdom_title_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
# Description: Manages earned and active kingdom titles.

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.kingdom_history_service import log_event

TITLE_MAP = {
    1: "Defender of the Realm",
    2: "Master Strategist",
    3: "Warden of the North",
}


def get_title_name_from_id(honor_reward_id: int) -> Optional[str]:
    """Return the title string mapped to the given ID."""
    return TITLE_MAP.get(honor_reward_id)

logger = logging.getLogger(__name__)


def award_title(db: Session, kingdom_id: int, title: str) -> None:
    """
    Grants a new title to the kingdom if not already earned.

    Args:
        db (Session): SQLAlchemy DB session
        kingdom_id (int): Target kingdom ID
        title (str): Title string to award

    Returns:
        None
    """
    try:
        row = db.execute(
            text(
                """
                SELECT 1 FROM kingdom_titles
                 WHERE kingdom_id = :kid AND title = :title
            """
            ),
            {"kid": kingdom_id, "title": title},
        ).fetchone()

        if row:
            return  # Title already exists

        db.execute(
            text(
                """
                INSERT INTO kingdom_titles (kingdom_id, title)
                VALUES (:kid, :title)
            """
            ),
            {"kid": kingdom_id, "title": title},
        )

        log_event(db, kingdom_id, "TITLE_AWARDED", title)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to award title '%s' to kingdom %d", title, kingdom_id)
        raise RuntimeError("Error awarding kingdom title") from exc


def list_titles(db: Session, kingdom_id: int) -> list[dict]:
    """
    Lists all titles earned by a kingdom in reverse chronological order.

    Returns:
        list of dicts: Each dict has keys: title, awarded_at
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT title, awarded_at
                  FROM kingdom_titles
                 WHERE kingdom_id = :kid
                 ORDER BY awarded_at DESC
            """
            ),
            {"kid": kingdom_id},
        ).fetchall()

        return [{"title": r[0], "awarded_at": r[1]} for r in rows]

    except SQLAlchemyError:
        logger.exception("Failed to list titles for kingdom %d", kingdom_id)
        return []


def set_active_title(db: Session, kingdom_id: int, title: Optional[str]) -> None:
    """
    Sets a display title for the kingdom. If None, clears the active title.

    Args:
        title (Optional[str]): Can be None to clear title.
    """
    try:
        if title is None:
            db.execute(
                text(
                    """
                    UPDATE kingdoms
                       SET customizations = customizations - 'active_title'
                     WHERE kingdom_id = :kid
                    """
                ),
                {"kid": kingdom_id},
            )
        else:
            db.execute(
                text(
                    """
                    UPDATE kingdoms
                       SET customizations = customizations ||
                           jsonb_build_object('active_title', :title)
                     WHERE kingdom_id = :kid
                    """
                ),
                {"title": title, "kid": kingdom_id},
            )
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to set active title for kingdom %d", kingdom_id)
        raise RuntimeError("Error setting active title") from exc


def get_active_title(db: Session, kingdom_id: int) -> Optional[str]:
    """
    Retrieves the currently active title of a kingdom.

    Returns:
        str or None: The active title string or None if not set.
    """
    try:
        row = db.execute(
            text(
                """
                SELECT customizations ->> 'active_title'
                  FROM kingdoms
                 WHERE kingdom_id = :kid
                """
            ),
            {"kid": kingdom_id},
        ).fetchone()

        return row[0] if row else None

    except SQLAlchemyError:
        logger.exception("Failed to get active title for kingdom %d", kingdom_id)
        return None
