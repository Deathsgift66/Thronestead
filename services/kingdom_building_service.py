# Project Name: Thronestead©
# File Name: kingdom_building_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66
"""Service logic for managing kingdom buildings across villages."""

from __future__ import annotations
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------

def _validate_building_id(db: Session, building_id: int) -> None:
    """Ensure building ID exists in the catalogue."""
    row = db.execute(
        text("SELECT 1 FROM building_catalogue WHERE building_id = :bid"),
        {"bid": building_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Building type does not exist.")

# ------------------------------------------------------------------------------
# Public Service Functions
# ------------------------------------------------------------------------------

def list_buildings(db: Session, village_id: int) -> list[dict]:
    """Return all buildings in a village with metadata from catalogue."""
    rows = db.execute(
        text(
            """
            SELECT vb.building_id, vb.level, vb.construction_status,
                   vb.started_at, vb.completed_at,
                   bc.name, bc.tier, bc.production_type, bc.modifiers
              FROM village_buildings vb
              JOIN building_catalogue bc ON vb.building_id = bc.building_id
             WHERE vb.village_id = :vid
             ORDER BY bc.tier, bc.name
            """
        ),
        {"vid": village_id},
    ).fetchall()

    return [dict(r._mapping) for r in rows]


def construct_building(
    db: Session,
    village_id: int,
    building_id: int,
    initiated_by: str,
    construction_time_seconds: int,
    replace_existing: bool = False
) -> int:
    """Begin or restart construction on a building in the village.

    Returns the `village_buildings.id` for the row.
    """
    _validate_building_id(db, building_id)

    # Optionally remove the existing structure
    if replace_existing:
        db.execute(
            text("DELETE FROM village_buildings WHERE village_id = :vid AND building_id = :bid"),
            {"vid": village_id, "bid": building_id}
        )

    # Start construction
    result = db.execute(
        text(
            """
            INSERT INTO village_buildings (
                village_id, building_id, level,
                construction_status, started_at, completed_at,
                initiated_by
            ) VALUES (
                :vid, :bid, 1,
                'in_progress', now(), now() + (:duration * interval '1 second'),
                :uid
            ) RETURNING id
            """
        ),
        {"vid": village_id, "bid": building_id, "duration": construction_time_seconds, "uid": initiated_by},
    )

    db.commit()
    row = result.fetchone()
    return row[0] if row else 0


def upgrade_building(
    db: Session,
    village_id: int,
    building_id: int,
    initiated_by: str,
    construction_time_seconds: int
) -> None:
    """Initiate an upgrade to the next level of the given building."""
    row = db.execute(
        text(
            """
            SELECT id, level FROM village_buildings
             WHERE village_id = :vid AND building_id = :bid
               AND construction_status = 'complete'
            """
        ),
        {"vid": village_id, "bid": building_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="Building not found or already upgrading")

    vb_id, current_level = row
    next_level = current_level + 1

    db.execute(
        text(
            """
            UPDATE village_buildings
               SET level = :lvl,
                   construction_status = 'in_progress',
                   started_at = now(),
                   completed_at = now() + (:duration * interval '1 second'),
                   initiated_by = :uid
             WHERE id = :vbid
            """
        ),
        {
            "lvl": next_level,
            "duration": construction_time_seconds,
            "uid": initiated_by,
            "vbid": vb_id,
        }
    )
    db.commit()


def mark_completed_buildings(db: Session) -> int:
    """Mark any completed building constructions as 'complete'."""
    result = db.execute(
        text(
            """
            UPDATE village_buildings
               SET construction_status = 'complete',
                   last_updated = now()
             WHERE construction_status = 'in_progress'
               AND completed_at <= now()
            """
        )
    )
    db.commit()
    return getattr(result, "rowcount", 0)


def get_building_level(
    db: Session, village_id: int, building_id: int
) -> Optional[int]:
    """Return the current level of a specific building, if it exists."""
    row = db.execute(
        text(
            """
            SELECT level FROM village_buildings
             WHERE village_id = :vid AND building_id = :bid
               AND construction_status = 'complete'
            """
        ),
        {"vid": village_id, "bid": building_id},
    ).fetchone()
    return row[0] if row else None


def delete_building(db: Session, village_id: int, building_id: int) -> None:
    """Remove a building from the village."""
    db.execute(
        text(
            """
            DELETE FROM village_buildings
             WHERE village_id = :vid AND building_id = :bid
            """
        ),
        {"vid": village_id, "bid": building_id}
    )
    db.commit()


def count_buildings_by_type(
    db: Session, kingdom_id: int, production_type: str
) -> int:
    """Count completed buildings of a specific type owned by a kingdom."""
    row = db.execute(
        text(
            """
            SELECT COUNT(*) FROM village_buildings vb
             JOIN kingdom_villages kv ON vb.village_id = kv.village_id
             JOIN building_catalogue bc ON vb.building_id = bc.building_id
            WHERE kv.kingdom_id = :kid
              AND vb.construction_status = 'complete'
              AND bc.production_type = :ptype
            """
        ),
        {"kid": kingdom_id, "ptype": production_type}
    ).fetchone()
    return row[0] if row else 0
