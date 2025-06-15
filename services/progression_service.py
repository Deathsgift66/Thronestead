# Project Name: Kingmakers Rise©
# File Name: progression_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Utility service for calculating troop slots, verifying progression gates, and merging live gameplay modifiers.

import json
import logging
import time

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
        prestige_scores,
        kingdom_treaties,
        kingdom_spies,
        global_game_settings,
    )
except ImportError:
    vip_levels = {}
    prestige_scores = {}
    kingdom_treaties = {}
    kingdom_spies = {}
    global_game_settings = {}

logger = logging.getLogger(__name__)

# Cached modifier data to reduce expensive aggregation queries.
_modifier_cache: dict[int, tuple[float, dict]] = {}
# Number of seconds before cached modifiers expire.
_CACHE_TTL = 60

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
                       COALESCE(rb.bonus_value::integer, 0)
                  FROM kingdom_troop_slots kts
                  JOIN kingdoms k ON k.kingdom_id = kts.kingdom_id
             LEFT JOIN region_bonuses rb ON rb.region_code = k.region
                                        AND rb.bonus_type = 'base_slots'
                 WHERE kts.kingdom_id = :kid
            """),

            {"kid": kingdom_id},
        ).fetchone()

        if not result:
            return 0

        base, buildings, tech, projects, events = result
        return base + buildings + tech + projects + events

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


def _region_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return modifiers granted by the kingdom's region."""
    region_code = db.execute(
        text("SELECT region FROM kingdoms WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).scalar()
    if not region_code:
        return {}
    rows = db.execute(
        text(

            "SELECT bonus_type, bonus_value FROM region_bonuses WHERE region_code = :code"

        ),
        {"code": region_code},
    ).fetchall()
    if not rows:
        return {}

    mods: dict = {}
    for btype, val in rows:
        bucket = mods.setdefault(btype, {})
        bucket["value"] = val
    return mods



def _tech_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return modifiers from completed research techs."""
    rows = db.execute(
        text(
            """
            SELECT tc.modifiers FROM kingdom_research_tracking krt
            JOIN tech_catalogue tc ON tc.tech_code = krt.tech_code
            WHERE krt.kingdom_id = :kid AND krt.status = 'completed'
        """
        ),
        {"kid": kingdom_id},
    ).fetchall()
    mods: dict = {}
    for (m,) in rows:
        _merge_modifiers(mods, m or {})
    return mods


def _temple_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return modifiers from active temples."""
    rows = db.execute(
        text(
            """
            SELECT bc.modifiers FROM village_buildings vb
            JOIN kingdom_villages kv ON vb.village_id = kv.village_id
            JOIN building_catalogue bc ON vb.building_id = bc.building_id
            WHERE kv.kingdom_id = :kid
              AND bc.production_type = 'temple'
              AND vb.construction_status = 'complete'
        """
        ),
        {"kid": kingdom_id},
    ).fetchall()
    mods: dict = {}
    for (m,) in rows:
        _merge_modifiers(mods, m or {})
    return mods


def _kingdom_project_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return modifiers from a kingdom's completed projects."""
    rows = db.execute(
        text(
            """
            SELECT pc.modifiers FROM projects_player pp
            JOIN project_player_catalogue pc ON pp.project_code = pc.project_code
            WHERE pp.kingdom_id = :kid
        """
        ),
        {"kid": kingdom_id},
    ).fetchall()
    mods: dict = {}
    for (m,) in rows:
        _merge_modifiers(mods, m or {})
    return mods


def _alliance_project_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return modifiers from alliance projects."""
    rows = db.execute(
        text(
            """
            SELECT pa.active_bonus FROM projects_alliance pa
            WHERE pa.alliance_id IN (
                SELECT alliance_id FROM alliance_members
                WHERE user_id = (SELECT user_id FROM kingdoms WHERE kingdom_id = :kid)
            )
              AND pa.is_active = true
              AND pa.build_state = 'completed'
        """
        ),
        {"kid": kingdom_id},
    ).fetchall()
    mods: dict = {}
    for (m,) in rows:
        if m:
            try:
                data = json.loads(m)
            except Exception:
                data = {}
            _merge_modifiers(mods, data)
    return mods


def _vip_modifiers(_: Session, kingdom_id: int) -> dict:
    """Return modifiers from the VIP level cache."""
    level = vip_levels.get(str(kingdom_id), 0)
    return global_game_settings.get("vip_perks", {}).get(level, {})


def _prestige_modifiers(_: Session, kingdom_id: int) -> dict:
    """Return modifiers based on prestige score."""
    score = prestige_scores.get(str(kingdom_id), 0)
    if not score:
        return {}
    return {"combat_bonus": {"prestige": score // 100}}


def _village_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return production modifiers from village count."""
    count = db.execute(
        text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).scalar()
    if not count:
        return {}
    return {"production_bonus": {"villages": count}}


def _treaty_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return modifiers from active treaties stored in the database."""
    rows = db.execute(
        text(
            """
            SELECT tm.effect_type, tm.target, tm.magnitude
              FROM kingdom_treaties kt
              JOIN treaty_modifiers tm ON tm.treaty_id = kt.treaty_id
             WHERE (kt.kingdom_id = :kid OR kt.partner_kingdom_id = :kid)
               AND kt.status = 'active'
            """
        ),
        {"kid": kingdom_id},
    ).fetchall()
    mods: dict = {}
    for effect, target, magnitude in rows:
        if magnitude is None:
            continue
        bucket = mods.setdefault(effect, {})
        bucket[target] = bucket.get(target, 0) + float(magnitude)
    return mods


def _spy_modifiers(_: Session, kingdom_id: int) -> dict:
    """Return modifiers provided by an active spy."""
    spy = kingdom_spies.get(kingdom_id)
    return spy.get("modifiers", {}) if spy else {}


def _global_event_modifiers(_: Session, __: int) -> dict:
    """Return global event modifiers."""
    return global_game_settings.get("event_modifiers", {})



def get_total_modifiers(db: Session, kingdom_id: int, *, use_cache: bool = True) -> dict:
    """Return aggregated modifiers for a kingdom with optional caching."""

    if use_cache:
        cached = _modifier_cache.get(kingdom_id)
        if cached and (time.time() - cached[0] < _CACHE_TTL):
            return cached[1]

    total = {
        "resource_bonus": {},
        "troop_bonus": {},
        "combat_bonus": {},
        "defense_bonus": {},
        "economic_bonus": {},
        "production_bonus": {},
    }

    sources = [
        _region_modifiers,
        _tech_modifiers,
        _temple_modifiers,
        _kingdom_project_modifiers,
        _alliance_project_modifiers,
        _vip_modifiers,
        _prestige_modifiers,
        _village_modifiers,
        _treaty_modifiers,
        _spy_modifiers,
        _global_event_modifiers,
    ]

    for func in sources:
        try:
            mods = func(db, kingdom_id)
            _merge_modifiers(total, mods)
        except Exception as e:
            logger.warning("%s error: %s", func.__name__, e)

    if use_cache:
        _modifier_cache[kingdom_id] = (time.time(), total)

    return total
