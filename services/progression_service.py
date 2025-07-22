# Project Name: Thronestead©
# File Name: progression_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
# Description: Utility service for calculating troop slots, verifying progression gates, and merging live gameplay modifiers.

import logging
import time
from threading import Lock
from typing import Dict, Set
from services.modifiers_utils import (
    parse_json_field,
    merge_modifiers_with_rules,
)

from fastapi import HTTPException

from services.sqlalchemy_support import Session, SQLAlchemyError, text

# Optional in-memory/game-state sources
try:
    from backend.data import (
        global_game_settings,
        kingdom_spies,
        kingdom_treaties,
        prestige_scores,
        castle_progression_state,
        vip_levels,
    )
except ImportError:
    vip_levels = {}
    prestige_scores = {}
    kingdom_treaties = {}
    kingdom_spies = {}
    global_game_settings = {}
    castle_progression_state = {}

from .faith_service import _get_faith_modifiers
from services.modifiers_utils import (
    _merge_modifiers,
    invalidate_cache,
    _modifier_cache,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------
# Simplified In-Memory Progression State (for tests)
# --------------------------------------------------------

# Lock protecting state mutations when used in async tests
_state_lock = Lock()

# Castle level tracked in memory
castle_state: Dict[str, int] = {"level": 1}

# Sets/dicts for nobles and knights
nobles: Set[str] = set()
knights: Dict[str, Dict[str, int]] = {}


def progress_castle() -> int:
    """Increase the castle level by one."""
    with _state_lock:
        new_level = castle_state.get("level", 1) + 1
        castle_state["level"] = new_level
        logger.info("🏰 Castle leveled up! New level: %s", new_level)
        return new_level


def add_noble(name: str) -> None:
    """Add a noble if not already present."""
    with _state_lock:
        added = name not in nobles
        nobles.add(name)
        if added:
            logger.info("👑 Noble '%s' added.", name)
        else:
            logger.debug("Noble '%s' already exists.", name)


def remove_noble(name: str) -> None:
    """Remove a noble if they exist."""
    with _state_lock:
        existed = name in nobles
        nobles.discard(name)
        if existed:
            logger.info("❌ Noble '%s' removed.", name)
        else:
            logger.debug("Noble '%s' not found.", name)


def add_knight(knight_id: str, rank: int = 1) -> None:
    """Register a new knight."""
    with _state_lock:
        if knight_id in knights:
            logger.debug("Knight '%s' already exists.", knight_id)
            return
        knights[knight_id] = {"rank": rank}
        logger.info("🛡️ Knight '%s' added with rank %s.", knight_id, rank)


def promote_knight(knight_id: str) -> int:
    """Promote a knight to the next rank and return the new rank."""
    with _state_lock:
        knight = knights.get(knight_id)
        if not knight:
            logger.error("⚠️ Cannot promote: Knight '%s' not found.", knight_id)
            raise ValueError("Knight not found")
        knight["rank"] += 1
        new_rank = knight["rank"]
        logger.info("⬆️ Knight '%s' promoted to rank %s.", knight_id, new_rank)
        return new_rank


def get_state() -> Dict[str, object]:
    """Return a snapshot of the current progression state."""
    with _state_lock:
        return {
            "castle": castle_state.copy(),
            "nobles": set(nobles),
            "knights": {k: v.copy() for k, v in knights.items()},
        }


def reset_state() -> None:
    """Reset all in-memory progression data."""
    with _state_lock:
        castle_state.update({"level": 1})
        nobles.clear()
        knights.clear()

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
            text(
                """
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
            """
            ),
            {"kid": kingdom_id},
        ).fetchone()

        if not result:
            return 0

        return sum(result)

    except SQLAlchemyError as exc:
        logger.warning("Failed to calculate troop slots: %s", exc)
        return 0


def check_troop_slots(db: Session, kingdom_id: int, troops_requested: int) -> None:
    """
    Raises an HTTP 400 if requested troops exceed available slots.
    """
    try:
        row = db.execute(
            text("SELECT used_slots FROM kingdom_troop_slots WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()

        used = row[0] if row else 0
        total = calculate_troop_slots(db, kingdom_id)

        if used + troops_requested > total:
            raise HTTPException(status_code=400, detail="Not enough troop slots")

    except SQLAlchemyError:
        logger.exception("Troop slot check failed for kingdom %d", kingdom_id)
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
    *,
    use_cache: bool = True,
) -> None:
    """
    Verifies that a kingdom meets progression thresholds.

    Raises:
        HTTPException(403) if any requirement is not satisfied.
    """
    level = None
    nobles = None
    knights = None

    if use_cache:
        prog = castle_progression_state.get(kingdom_id)
        if prog:
            level = prog.get("castle_level")
            nobles = prog.get("nobles")
            knights = prog.get("knights")

    if level is None:
        level = (
            db.execute(
                text(
                    "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
                ),
                {"kid": kingdom_id},
            ).scalar()
            or 1
        )
    if required_nobles > 0 and nobles is None:
        nobles = (
            db.execute(
                text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
                {"kid": kingdom_id},
            ).scalar()
            or 0
        )
    if required_knights > 0 and knights is None:
        knights = (
            db.execute(
                text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
                {"kid": kingdom_id},
            ).scalar()
            or 0
        )

    if level < required_castle_level:
        raise HTTPException(status_code=403, detail="Castle level too low")

    if required_nobles > 0 and nobles is not None and nobles < required_nobles:
        raise HTTPException(status_code=403, detail="Not enough nobles")

    if required_knights > 0 and knights is not None and knights < required_knights:
        raise HTTPException(status_code=403, detail="Not enough knights")


# --------------------------------------------------------
# Modifier Aggregation
# --------------------------------------------------------



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
        try:
            val_num = float(val)
        except (TypeError, ValueError):
            continue
        bucket["value"] = bucket.get("value", 0) + val_num
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
              AND (pp.ends_at IS NULL OR pp.ends_at > now())
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
            _merge_modifiers(mods, parse_json_field(m))
    return mods


def _vip_modifiers(_: Session, kingdom_id: int) -> dict:
    """Return modifiers from the VIP level cache."""
    level = vip_levels.get(str(kingdom_id), 0)
    return global_game_settings.get("vip_perks", {}).get(level, {})


def _prestige_modifiers(_: Session, kingdom_id: int) -> dict:
    """Return an empty modifier set since prestige no longer affects combat."""
    _ = prestige_scores.get(str(kingdom_id), 0)
    return {}


def _village_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return production modifiers from village count."""
    count = db.execute(
        text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).scalar()
    if not count:
        return {}
    return {"production_bonus": {"villages": count}}


def _village_modifier_rows(db: Session, kingdom_id: int) -> dict:
    """Return modifiers from active rows in village_modifiers."""
    rows = db.execute(
        text(
            """
            SELECT vm.resource_bonus,
                   vm.troop_bonus,
                   vm.construction_speed_bonus,
                   vm.defense_bonus,
                   vm.trade_bonus,
                   vm.stacking_rules
              FROM village_modifiers vm
              JOIN kingdom_villages kv ON kv.village_id = vm.village_id
             WHERE kv.kingdom_id = :kid
               AND (vm.expires_at IS NULL OR vm.expires_at > now())
            """
        ),
        {"kid": kingdom_id},
    ).fetchall()
    mods: dict = {}
    for rb, tb, csb, dbonus, tradeb, rules in rows:
        row_mod: dict = {}
        if rb:
            row_mod["resource_bonus"] = parse_json_field(rb)
        if tb:
            row_mod["troop_bonus"] = parse_json_field(tb)
        if csb:
            row_mod.setdefault("production_bonus", {})[
                "construction_speed_bonus"
            ] = float(csb)
        if dbonus:
            row_mod.setdefault("defense_bonus", {})["village"] = float(dbonus)
        if tradeb:
            row_mod.setdefault("economic_bonus", {})["trade_bonus"] = float(tradeb)
        r_rules = parse_json_field(rules) or {}
        merge_modifiers_with_rules(mods, row_mod, r_rules)
    return mods


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


# Ordered list of all modifier source functions used by ``get_total_modifiers``.
_MODIFIER_SOURCES = [
    _region_modifiers,
    _tech_modifiers,
    _temple_modifiers,
    _kingdom_project_modifiers,
    _alliance_project_modifiers,
    _vip_modifiers,
    _get_faith_modifiers,
    _prestige_modifiers,
    _village_modifiers,
    _village_modifier_rows,
    _treaty_modifiers,
    _spy_modifiers,
    _global_event_modifiers,
]


def get_total_modifiers(
    db: Session, kingdom_id: int, *, use_cache: bool = True
) -> dict:
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

    for func in _MODIFIER_SOURCES:
        try:
            mods = func(db, kingdom_id)
            _merge_modifiers(total, mods)
        except Exception as e:
            logger.warning("%s error: %s", func.__name__, e)

    if use_cache:
        _modifier_cache[kingdom_id] = (time.time(), total)

    return total

