# Project Name: Kingmakers Rise©
# File Name: progression_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Utility service for calculating troop slots, verifying progression gates, and merging live gameplay modifiers.

import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore

# Optional in-memory/game-state sources
try:
    from backend.data import (
        vip_levels,
        player_titles,
        prestige_scores,
        kingdom_treaties,
        alliance_treaties,
        kingdom_spies,
        global_game_settings,
    )
except ImportError:
    vip_levels = {}
    player_titles = {}
    prestige_scores = {}
    kingdom_treaties = {}
    alliance_treaties = {}
    kingdom_spies = {}
    global_game_settings = {}

logger = logging.getLogger(__name__)

# --------------------------------------------------------
# Troop Slot Calculation
# --------------------------------------------------------

def calculate_troop_slots(db: Session, kingdom_id: int) -> int:
    """
    Calculates total available troop slots for a kingdom from all bonus sources.

    Returns:
        int: total number of slots
    """
    try:
        result = db.execute(
            text("""
                SELECT kts.base_slots,
                       kts.slots_from_buildings,
                       kts.slots_from_tech,
                       kts.slots_from_projects,
                       kts.slots_from_events,
                       COALESCE((rc.troop_bonus ->> 'base_slots')::integer, 0)
                  FROM kingdom_troop_slots kts
                  JOIN kingdoms k ON k.kingdom_id = kts.kingdom_id
             LEFT JOIN region_catalogue rc ON rc.region_code = k.region
                 WHERE kts.kingdom_id = :kid
            """),
            {"kid": kingdom_id},
        ).fetchone()

        if not result:
            return 0

        base, buildings, tech, projects, events, region_bonus = result
        return base + buildings + tech + projects + events + region_bonus

    except SQLAlchemyError as e:
        logger.warning("Failed to calculate troop slots: %s", e)
        return 0


def check_troop_slots(db: Session, kingdom_id: int, troops_requested: int) -> None:
    """
    Raises an HTTP 400 if requested troops exceed available slots.
    """
    try:
        row = db.execute(
            text("""
                SELECT base_slots, slots_from_buildings, slots_from_tech,
                       slots_from_projects, slots_from_events, used_slots
                  FROM kingdom_troop_slots
                 WHERE kingdom_id = :kid
            """),
            {"kid": kingdom_id},
        ).fetchone()

        if not row:
            total, used = 0, 0
        else:
            base, bld, tech, proj, evt, used = row
            total = base + bld + tech + proj + evt

        if used + troops_requested > total:
            raise HTTPException(status_code=400, detail="Not enough troop slots")

    except SQLAlchemyError as e:
        logger.warning("Troop slot check failed for kingdom %d", kingdom_id)
        raise HTTPException(status_code=500, detail="Slot verification error")


# --------------------------------------------------------
# Progression Requirements
# --------------------------------------------------------

def check_progression_requirements(
    db: Session,
    kingdom_id: int,
    required_castle_level: int = 0,
    required_nobles: int = 0,
    required_knights: int = 0,
) -> None:
    """
    Verifies that a kingdom meets progression thresholds.

    Raises:
        HTTPException(403) if any requirement is not satisfied.
    """
    # Castle level
    level = db.execute(
        text("SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).scalar() or 1

    if level < required_castle_level:
        raise HTTPException(status_code=403, detail="Castle level too low")

    # Noble count
    if required_nobles > 0:
        nobles = db.execute(
            text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).scalar() or 0
        if nobles < required_nobles:
            raise HTTPException(status_code=403, detail="Not enough nobles")

    # Knight count
    if required_knights > 0:
        knights = db.execute(
            text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).scalar() or 0
        if knights < required_knights:
            raise HTTPException(status_code=403, detail="Not enough knights")


# --------------------------------------------------------
# Modifier Aggregation
# --------------------------------------------------------

def _merge_modifiers(target: dict, mods: dict) -> None:
    """
    Deep-merges modifier dictionaries into the target dict.
    """
    if not isinstance(mods, dict):
        return
    for cat, inner in mods.items():
        if not isinstance(inner, dict):
            continue
        bucket = target.setdefault(cat, {})
        for key, val in inner.items():
            bucket[key] = bucket.get(key, 0) + val


def get_total_modifiers(db: Session, kingdom_id: int) -> dict:
    """
    Aggregates all modifiers from regions, research, temples, projects, VIP, and other systems.

    Returns:
        dict: a nested dictionary of modifier categories and keys
    """
    total = {
        "resource_bonus": {},
        "troop_bonus": {},
        "combat_bonus": {},
        "defense_bonus": {},
        "economic_bonus": {},
        "production_bonus": {},
    }

    # Region Bonuses
    try:
        region_code = db.execute(
            text("SELECT region FROM kingdoms WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).scalar()
        if region_code:
            row = db.execute(
                text("SELECT resource_bonus, troop_bonus FROM region_catalogue WHERE region_code = :code"),
                {"code": region_code},
            ).fetchone()
            if row:
                _merge_modifiers(total, {
                    "resource_bonus": row[0] or {},
                    "troop_bonus": row[1] or {},
                })
    except Exception as e:
        logger.warning("Region bonus error: %s", e)

    # Completed Techs
    try:
        rows = db.execute(
            text("""
                SELECT tc.modifiers FROM kingdom_research_tracking krt
                JOIN tech_catalogue tc ON tc.tech_code = krt.tech_code
                WHERE krt.kingdom_id = :kid AND krt.status = 'completed'
            """),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as e:
        logger.warning("Tech modifier error: %s", e)

    # Active Temples
    try:
        rows = db.execute(
            text("""
                SELECT bc.modifiers FROM village_buildings vb
                JOIN kingdom_villages kv ON vb.village_id = kv.village_id
                JOIN building_catalogue bc ON vb.building_id = bc.building_id
                WHERE kv.kingdom_id = :kid
                  AND bc.production_type = 'temple'
                  AND vb.construction_status = 'complete'
            """),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as e:
        logger.warning("Temple modifier error: %s", e)

    # Kingdom Projects
    try:
        rows = db.execute(
            text("""
                SELECT pc.modifiers FROM projects_player pp
                JOIN project_player_catalogue pc ON pp.project_code = pc.project_code
                WHERE pp.kingdom_id = :kid
            """),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as e:
        logger.warning("Kingdom project modifier error: %s", e)

    # Alliance Projects
    try:
        rows = db.execute(
            text("""
                SELECT pa.modifiers FROM projects_alliance pa
                WHERE pa.alliance_id IN (
                    SELECT alliance_id FROM alliance_members
                    WHERE user_id = (SELECT user_id FROM kingdoms WHERE kingdom_id = :kid)
                )
                  AND pa.is_active = true
                  AND pa.build_state = 'completed'
            """),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as e:
        logger.warning("Alliance project modifier error: %s", e)

    # VIP Perks
    try:
        level = vip_levels.get(str(kingdom_id), 0)
        perks = global_game_settings.get("vip_perks", {}).get(level, {})
        _merge_modifiers(total, perks)
    except Exception as e:
        logger.warning("VIP modifier error: %s", e)

    # Prestige Score
    try:
        score = prestige_scores.get(str(kingdom_id), 0)
        if score:
            _merge_modifiers(total, {"combat_bonus": {"prestige": score // 100}})
    except Exception as e:
        logger.warning("Prestige bonus error: %s", e)

    # Village Productivity
    try:
        count = db.execute(
            text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).scalar()
        if count:
            _merge_modifiers(total, {"production_bonus": {"villages": count}})
    except Exception as e:
        logger.warning("Village bonus error: %s", e)

    # Treaty Modifiers
    try:
        for treaty in kingdom_treaties.get(kingdom_id, []):
            _merge_modifiers(total, treaty.get("modifiers", {}))
    except Exception as e:
        logger.warning("Treaty modifier error: %s", e)

    # Spy Modifiers
    try:
        spy = kingdom_spies.get(kingdom_id)
        if spy:
            _merge_modifiers(total, spy.get("modifiers", {}))
    except Exception as e:
        logger.warning("Spy modifier error: %s", e)

    # Global Events
    try:
        _merge_modifiers(total, global_game_settings.get("event_modifiers", {}))
    except Exception as e:
        logger.warning("Global event modifier error: %s", e)

    return total
