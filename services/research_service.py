# Project Name: Thronestead©
# File Name: research_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Service functions for managing kingdom technology research.

from __future__ import annotations

import logging
from datetime import datetime, timedelta

try:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Start a New Research
# -------------------------------------------------------------


def start_research(db: Session, kingdom_id: int, tech_code: str) -> datetime:
    """
    Begin research on a technology for the given kingdom.

    - Validates that the tech is active and prerequisites are met.
    - Updates or inserts into `kingdom_research_tracking`.
    - Returns the `ends_at` datetime.

    Raises:
        ValueError: If tech does not exist or prerequisites are unmet.
    """
    try:
        # Check catalog entry
        duration_row = db.execute(
            text(
                """
                SELECT duration_hours, prerequisites
                  FROM tech_catalogue
                 WHERE tech_code = :code AND is_active = true
            """
            ),
            {"code": tech_code},
        ).fetchone()

        if not duration_row:
            raise ValueError("Tech not found or not active")

        duration_hours, prereqs = duration_row
        prereqs = prereqs or []

        # Check prerequisites
        if prereqs:
            rows = db.execute(
                text(
                    """
                    SELECT tech_code FROM kingdom_research_tracking
                     WHERE kingdom_id = :kid AND status = 'completed'
                """
                ),
                {"kid": kingdom_id},
            ).fetchall()
            completed = {r[0] for r in rows}
            if not set(prereqs).issubset(completed):
                raise ValueError("Missing research prerequisites")

        ends_at = datetime.utcnow() + timedelta(hours=duration_hours or 0)

        # Insert or update
        db.execute(
            text(
                """
                INSERT INTO kingdom_research_tracking (
                    kingdom_id, tech_code, status, progress, ends_at
                ) VALUES (:kid, :code, 'active', 0, :end)
                ON CONFLICT (kingdom_id, tech_code)
                DO UPDATE SET
                    status = 'active',
                    progress = 0,
                    ends_at = EXCLUDED.ends_at
            """
            ),
            {"kid": kingdom_id, "code": tech_code, "end": ends_at},
        )
        db.commit()
        return ends_at

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "Failed to start research %s for kingdom %d", tech_code, kingdom_id
        )
        raise RuntimeError("Research initiation failed") from exc


# -------------------------------------------------------------
# Complete Expired Research
# -------------------------------------------------------------


def complete_finished_research(db: Session, kingdom_id: int) -> None:
    """
    Automatically marks expired research rows (based on ends_at) as completed.
    """
    try:
        db.execute(
            text(
                """
                UPDATE kingdom_research_tracking
                   SET status = 'completed', progress = 100
                 WHERE kingdom_id = :kid
                   AND status = 'active'
                   AND ends_at <= now()
            """
            ),
            {"kid": kingdom_id},
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "Failed to complete expired research for kingdom %d", kingdom_id
        )
        raise RuntimeError("Research completion update failed") from exc


# -------------------------------------------------------------
# Fetch All Research Entries
# -------------------------------------------------------------


def list_research(
    db: Session, kingdom_id: int, category: str | None = None
) -> list[dict]:
    """
    Returns all research tracking rows for the given kingdom.

    Args:
        db: database session
        kingdom_id: kingdom identifier
        category: optional tech category to filter by

    Returns:
        list of dicts with: tech_code, status, progress, ends_at
    """
    try:
        # Auto-complete any research that has finished since the last check
        complete_finished_research(db, kingdom_id)

        query = """
                SELECT tr.tech_code, tr.status, tr.progress, tr.ends_at
                  FROM kingdom_research_tracking AS tr
                  JOIN tech_catalogue AS tc ON tc.tech_code = tr.tech_code
                 WHERE tr.kingdom_id = :kid
        """
        params = {"kid": kingdom_id}
        if category:
            query += " AND tc.category = :category"
            params["category"] = category
        query += " ORDER BY tr.tech_code"

        rows = db.execute(text(query), params).fetchall()

        return [
            {"tech_code": r[0], "status": r[1], "progress": r[2], "ends_at": r[3]}
            for r in rows
        ]

    except SQLAlchemyError:
        logger.exception("Failed to fetch research list for kingdom %d", kingdom_id)
        return []


# -------------------------------------------------------------
# Check if Tech is Completed
# -------------------------------------------------------------


def is_tech_completed(db: Session, kingdom_id: int, tech_code: str) -> bool:
    """
    Returns True if the kingdom has completed the given tech.
    """
    try:
        row = db.execute(
            text(
                """
                SELECT 1 FROM kingdom_research_tracking
                 WHERE kingdom_id = :kid
                   AND tech_code = :code
                   AND status = 'completed'
            """
            ),
            {"kid": kingdom_id, "code": tech_code},
        ).fetchone()
        return row is not None

    except SQLAlchemyError:
        logger.warning("Failed to verify tech completion for %s", tech_code)
        return False
