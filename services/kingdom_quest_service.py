# Project Name: Thronestead©
# File Name: kingdom_quest_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Service functions for handling individual kingdom quest tracking.

from datetime import datetime, timedelta
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover
    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

logger = logging.getLogger(__name__)


# -----------------------------------------------------
# 🚀 Start or Reset a Quest
# -----------------------------------------------------

def start_quest(db: Session, kingdom_id: int, quest_code: str, started_by: str) -> datetime:
    """
    Starts (or resets) a quest for a given kingdom.

    Args:
        db: Database session.
        kingdom_id: ID of the kingdom.
        quest_code: Quest identifier.
        started_by: User who initiated the quest.

    Returns:
        datetime: The computed `ends_at` timestamp for the quest duration.
    """
    try:
        # Fetch duration from quest catalog
        duration_row = db.execute(
            text("SELECT duration_hours FROM quest_kingdom_catalogue WHERE quest_code = :code"),
            {"code": quest_code},
        ).fetchone()
        if not duration_row:
            raise ValueError("Quest not found")

        duration_hours = duration_row[0] or 0
        ends_at = datetime.utcnow() + timedelta(hours=duration_hours)

        # Upsert the quest tracking row
        db.execute(
            text("""
                INSERT INTO quest_kingdom_tracking (
                    kingdom_id, quest_code, status, progress, progress_details,
                    ends_at, started_by, attempt_count, objective_progress,
                    is_complete
                ) VALUES (
                    :kid, :code, 'active', 0, '{}'::jsonb, :end, :uid, 1, 0,
                    false
                )
                ON CONFLICT (kingdom_id, quest_code)
                DO UPDATE SET
                    status = 'active',
                    progress = 0,
                    progress_details = '{}'::jsonb,
                    ends_at = EXCLUDED.ends_at,
                    started_by = EXCLUDED.started_by,
                    attempt_count = quest_kingdom_tracking.attempt_count + 1,
                    objective_progress = 0,
                    is_complete = false,
                    started_at = now(),
                    last_updated = now()
            """),
            {"kid": kingdom_id, "code": quest_code, "end": ends_at, "uid": started_by},
        )
        db.commit()
        return ends_at

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to start quest: %s for kingdom %d", quest_code, kingdom_id)
        raise RuntimeError("Failed to start quest") from e


# -----------------------------------------------------
# 🔄 Progress Update
# -----------------------------------------------------

def update_progress(db: Session, kingdom_id: int, quest_code: str, progress: int, details: dict, objective_progress: int | None = None) -> None:
    """
    Updates the progress and progress_details of an active quest.

    Args:
        db: Database session.
        kingdom_id: ID of the kingdom.
        quest_code: Quest identifier.
        progress: Numeric progress value.
        details: JSON-serializable dictionary of progress details.
    """
    try:
        db.execute(
            text("""
                UPDATE quest_kingdom_tracking
                   SET progress = :prog,
                       progress_details = :details,
                       last_updated = now(),
                       objective_progress = COALESCE(:obj_prog, objective_progress)
                 WHERE kingdom_id = :kid AND quest_code = :code
            """),
            {
                "kid": kingdom_id,
                "code": quest_code,
                "prog": progress,
                "details": details,
                "obj_prog": objective_progress,
            },
        )
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to update quest progress: %s", quest_code)
        raise RuntimeError("Failed to update quest progress") from e


# -----------------------------------------------------
# ✅ Completion & Cancellation
# -----------------------------------------------------

def complete_quest(db: Session, kingdom_id: int, quest_code: str) -> None:
    """
    Marks a quest as completed.

    Args:
        db: Database session.
        kingdom_id: ID of the kingdom.
        quest_code: Quest identifier.
    """
    try:
        db.execute(
            text("""
                UPDATE quest_kingdom_tracking
                   SET status = 'completed',
                       is_complete = true,
                       last_updated = now()
                 WHERE kingdom_id = :kid AND quest_code = :code
            """),
            {"kid": kingdom_id, "code": quest_code},
        )
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to complete quest: %s", quest_code)
        raise RuntimeError("Failed to mark quest completed") from e


def cancel_quest(db: Session, kingdom_id: int, quest_code: str) -> None:
    """
    Cancels an active quest.

    Args:
        db: Database session.
        kingdom_id: ID of the kingdom.
        quest_code: Quest identifier.
    """
    try:
        db.execute(
            text("""
                UPDATE quest_kingdom_tracking
                   SET status = 'cancelled', last_updated = now()
                 WHERE kingdom_id = :kid AND quest_code = :code
            """),
            {"kid": kingdom_id, "code": quest_code},
        )
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to cancel quest: %s", quest_code)
        raise RuntimeError("Failed to cancel quest") from e


# -----------------------------------------------------
# 🕓 Expiry Handler
# -----------------------------------------------------

def expire_quests(db: Session) -> int:
    """
    Expires all quests whose `ends_at` timestamp is past due and are still marked as 'active'.

    Returns:
        int: Number of quests expired.
    """
    try:
        result = db.execute(
            text("""
                UPDATE quest_kingdom_tracking
                   SET status = 'expired', last_updated = now()
                 WHERE status = 'active' AND ends_at < now()
            """)
        )
        db.commit()
        return getattr(result, "rowcount", 0)

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Failed to expire overdue quests")
        raise RuntimeError("Failed to expire quests") from e
