# Project Name: Thronestead©
# File Name: village_queue_service.py
# Version: 6.14.2025.20.13
"""Building construction queue logic for villages."""

from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Queue Management Helpers
# ---------------------------------------------------------------------------

def queue_building_upgrade(db: Session, village_id: int, building_type: str) -> int:
    """Queue the next level upgrade for a building.

    Raises:
        HTTPException: If the building is already under construction or queued.
    Returns:
        int: The queue_id of the inserted row.
    """

    # Check for existing construction on this building
    row = db.execute(
        text(
            """
            SELECT 1 FROM village_buildings
            WHERE village_id = :vid
              AND building_type = :bt
              AND construction_status = 'in_progress'
            """
        ),
        {"vid": village_id, "bt": building_type},
    ).fetchone()
    if row:
        raise HTTPException(400, "Building already under construction")

    # Check queue for this building
    row = db.execute(
        text(
            """
            SELECT 1 FROM village_queue
            WHERE village_id = :vid
              AND building_type = :bt
              AND status IN ('pending', 'in_progress')
            """
        ),
        {"vid": village_id, "bt": building_type},
    ).fetchone()
    if row:
        raise HTTPException(400, "Upgrade already queued")

    # Determine next level
    current = db.execute(
        text(
            "SELECT level FROM village_buildings WHERE village_id = :vid AND building_type = :bt"
        ),
        {"vid": village_id, "bt": building_type},
    ).fetchone()
    target_level = (current[0] if current else 0) + 1

    result = db.execute(
        text(
            """
            INSERT INTO village_queue (
                village_id, building_type, target_level,
                queued_at, status
            ) VALUES (
                :vid, :bt, :lvl, now(), 'pending'
            ) RETURNING queue_id
            """
        ),
        {"vid": village_id, "bt": building_type, "lvl": target_level},
    )
    db.commit()
    row = result.fetchone()
    return int(row[0]) if row else 0


def start_next_in_queue(db: Session, village_id: int) -> None:
    """Begin the next pending upgrade for a village, if available."""
    row = db.execute(
        text(
            """
            SELECT queue_id, building_type, target_level
            FROM village_queue
            WHERE village_id = :vid AND status = 'pending'
            ORDER BY queued_at
            LIMIT 1
            """
        ),
        {"vid": village_id},
    ).fetchone()
    if not row:
        return
    queue_id, building_type, target_level = row

    dur_row = db.execute(
        text("SELECT build_time_seconds FROM building_catalogue WHERE building_type = :bt"),
        {"bt": building_type},
    ).fetchone()
    duration = dur_row[0] if dur_row else 3600

    db.execute(
        text(
            """
            UPDATE village_queue
               SET status = 'in_progress',
                   starts_at = now(),
                   ends_at = now() + (:dur * interval '1 second')
             WHERE queue_id = :qid
            """
        ),
        {"dur": duration, "qid": queue_id},
    )
    db.commit()


def mark_completed_queued_buildings(db: Session) -> int:
    """Finalize any completed queued upgrades."""
    rows = db.execute(
        text(
            """
            SELECT queue_id, village_id, building_type, target_level
            FROM village_queue
            WHERE status = 'in_progress' AND ends_at <= now()
            """
        )
    ).fetchall()

    processed = 0
    for row in rows:
        qid, vid, btype, target = row
        db.execute(
            text(
                """
                INSERT INTO village_buildings (
                    village_id, building_type, level,
                    construction_status, ends_at
                ) VALUES (
                    :vid, :bt, :lvl, 'complete', now()
                )
                ON CONFLICT (village_id, building_type) DO UPDATE
                SET level = EXCLUDED.level,
                    construction_status = 'complete',
                    ends_at = now()
                """
            ),
            {"vid": vid, "bt": btype, "lvl": target},
        )
        db.execute(
            text("UPDATE village_queue SET status = 'completed' WHERE queue_id = :qid"),
            {"qid": qid},
        )
        db.commit()
        processed += 1
        start_next_in_queue(db, vid)

    return processed
