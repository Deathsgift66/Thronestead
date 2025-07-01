# Project Name: Thronestead©
# File Name: kingdom_building_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Service logic for managing kingdom buildings across villages."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from services import resource_service

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------


def _validate_building_id(db: Session, building_id: int) -> None:
    """Ensure building ID exists in the catalogue."""
    row = db.execute(
        text("SELECT 1 FROM building_catalogue WHERE building_id = :bid"),
        {"bid": building_id},
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
                   vb.construction_started_at, vb.construction_ends_at,
                   bc.building_name, bc.category, bc.production_type, bc.modifiers
              FROM village_buildings vb
              JOIN building_catalogue bc ON vb.building_id = bc.building_id
             WHERE vb.village_id = :vid
             ORDER BY bc.category, bc.building_id
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
    replace_existing: bool = False,
) -> int:
    """Begin or restart construction on a building in the village.

    Returns the `village_buildings.id` for the row.
    """
    _validate_building_id(db, building_id)

    # Optionally remove the existing structure
    if replace_existing:
        db.execute(
            text(
                "DELETE FROM village_buildings WHERE village_id = :vid AND building_id = :bid"
            ),
            {"vid": village_id, "bid": building_id},
        )

    # Ensure no other construction is active in this village
    active = db.execute(
        text(
            "SELECT 1 FROM village_buildings WHERE village_id = :vid AND construction_status = 'under_construction'"
        ),
        {"vid": village_id},
    ).fetchone()
    if active:
        raise HTTPException(400, "Another construction already in progress")

    # Start construction
    db.execute(
        text(
            """
            INSERT INTO village_buildings (
                village_id, building_id, level,
                construction_status,
                construction_started_at,
                construction_ends_at,
                constructed_by,
                is_under_construction
            ) VALUES (
                :vid, :bid, 1,
                'under_construction',
                now(),
                now() + (:duration * interval '1 second'),
                :uid,
                true
            )
            """
        ),
        {
            "vid": village_id,
            "bid": building_id,
            "duration": construction_time_seconds,
            "uid": initiated_by,
        },
    )

    db.commit()
    return 1


def upgrade_building(
    db: Session,
    kingdom_id: int,
    village_id: int,
    building_id: int,
    initiated_by: str,
    construction_time_seconds: int,
) -> None:
    """Initiate an upgrade to the next level of the given building."""
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

    if not row:
        raise HTTPException(
            status_code=400, detail="Building not found or already upgrading"
        )

    current_level = row[0]

    # Fetch the maximum allowed level for this building
    max_row = db.execute(
        text("SELECT max_level FROM building_catalogue WHERE building_id = :bid"),
        {"bid": building_id},
    ).fetchone()
    max_level = max_row[0] if max_row else None

    if max_level is not None and current_level >= max_level:
        raise HTTPException(status_code=400, detail="Building already at max level")

    next_level = current_level + 1

    # Determine resource costs for this upgrade
    cost_row = db.execute(
        text(
            "SELECT wood_cost, stone_cost, iron_cost, gold_cost, "
            "wood_plan_cost, iron_ingot_cost "
            "FROM building_catalogue WHERE building_id = :bid"
        ),
        {"bid": building_id},
    ).fetchone()

    spend_cost: dict[str, int] = {}
    if cost_row:
        wood_c, stone_c, iron_c, gold_c, planks_c, ingots_c = cost_row
        if wood_c:
            spend_cost["wood"] = int(wood_c) * next_level
        if stone_c:
            spend_cost["stone"] = int(stone_c) * next_level
        if iron_c:
            spend_cost["iron_ore"] = int(iron_c) * next_level
        if gold_c:
            spend_cost["gold"] = int(gold_c) * next_level
        if planks_c:
            spend_cost["wood_planks"] = int(planks_c) * next_level
        if ingots_c:
            spend_cost["iron_ingots"] = int(ingots_c) * next_level

    if spend_cost:
        resource_service.spend_resources(db, kingdom_id, spend_cost, commit=False)

    db.execute(
        text(
            """
            UPDATE village_buildings
               SET level = :lvl,
                   construction_status = 'under_construction',
                   construction_started_at = now(),
                   construction_ends_at = now() + (:duration * interval '1 second'),
                   constructed_by = :uid,
                   is_under_construction = true
             WHERE village_id = :vid AND building_id = :bid
            """
        ),
        {
            "lvl": next_level,
            "duration": construction_time_seconds,
            "uid": initiated_by,
            "vid": village_id,
            "bid": building_id,
        },
    )
    db.commit()


def mark_completed_buildings(db: Session) -> int:
    """Mark any completed building constructions as 'complete'."""
    result = db.execute(
        text(
            """
            UPDATE village_buildings
               SET construction_status = 'complete',
                   last_updated = now(),
                   is_under_construction = false
             WHERE construction_status = 'under_construction'
               AND construction_ends_at <= now()
            """
        )
    )
    db.commit()

    from services.village_queue_service import mark_completed_queued_buildings

    processed = mark_completed_queued_buildings(db)

    return getattr(result, "rowcount", 0) + processed


def get_building_level(db: Session, village_id: int, building_id: int) -> Optional[int]:
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
        {"vid": village_id, "bid": building_id},
    )
    db.commit()


def count_buildings_by_type(db: Session, kingdom_id: int, production_type: str) -> int:
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
        {"kid": kingdom_id, "ptype": production_type},
    ).fetchone()
    return row[0] if row else 0
