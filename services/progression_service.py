"""Utility service functions related to progression."""

import logging
from fastapi import HTTPException

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback for test environments
    text = lambda q: q
    Session = object

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
except ImportError:  # pragma: no cover - fallback when backend package missing
    vip_levels = {}
    player_titles = {}
    prestige_scores = {}
    kingdom_treaties = {}
    alliance_treaties = {}
    kingdom_spies = {}
    global_game_settings = {}


def get_active_alliance_treaties(db: Session, alliance_id: int) -> list[dict]:
    """Return active treaties for the given alliance."""
    try:
        rows = db.execute(
            text(
                """
                SELECT treaty_id, treaty_type, partner_alliance_id, signed_at
                FROM alliance_treaties
                WHERE (alliance_id = :aid OR partner_alliance_id = :aid)
                  AND status = 'active'
                ORDER BY signed_at DESC
                """
            ),
            {"aid": alliance_id},
        ).fetchall()
        return [
            {
                "treaty_id": r[0],
                "treaty_type": r[1],
                "partner_alliance_id": r[2],
                "signed_at": r[3],
            }
            for r in rows
        ]
    except Exception as exc:
        logging.warning("Failed to fetch alliance treaties: %s", exc)
        return []

def calculate_troop_slots(db: Session, kingdom_id: int) -> int:
    """Calculate and return the total troop slots for a kingdom.

    The database stores individual bonus columns. This helper aggregates them
    and returns the total. No table currently persists the total, so callers
    may persist the value if desired.
    """

    result = db.execute(
        text(
            """
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
            """
        ),
        {"kid": kingdom_id},
    ).fetchone()

    if not result:
        return 0

    (
        base_slots,
        building_bonus,
        tech_bonus,
        project_bonus,
        event_bonus,
        region_slots,
    ) = result

    total_slots = (
        base_slots
        + building_bonus
        + tech_bonus
        + project_bonus
        + event_bonus
        + region_slots
    )

    return total_slots


def check_progression_requirements(
    db: Session,
    kingdom_id: int,
    required_castle_level: int = 0,
    required_nobles: int = 0,
    required_knights: int = 0,
) -> None:
    """Validate progression requirements against the database.

    The function checks the player's castle level, the number of nobles and the
    number of knights. If any requirement is not satisfied an HTTP 403 error is
    raised.
    """

    # Castle level -------------------------------------------------------
    castle_row = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression"
            " WHERE kingdom_id = :kid"
        ),
        {"kid": kingdom_id},
    ).fetchone()
    castle_level = castle_row[0] if castle_row else 1
    if castle_level < required_castle_level:
        raise HTTPException(status_code=403, detail="Castle level too low")

    # Nobles count -------------------------------------------------------
    if required_nobles > 0:
        noble_row = db.execute(
            text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
        nobles = noble_row[0] if noble_row else 0
        if nobles < required_nobles:
            raise HTTPException(status_code=403, detail="Not enough nobles")

    # Knights count ------------------------------------------------------
    if required_knights > 0:
        knight_row = db.execute(
            text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
        knights = knight_row[0] if knight_row else 0
        if knights < required_knights:
            raise HTTPException(status_code=403, detail="Not enough knights")


def check_troop_slots(db: Session, kingdom_id: int, troops_requested: int) -> None:
    """Ensure the kingdom has enough free troop slots for a request."""

    record = db.execute(
        text(
            """
            SELECT base_slots,
                   slots_from_buildings,
                   slots_from_tech,
                   slots_from_projects,
                   slots_from_events,
                   used_slots
            FROM kingdom_troop_slots
            WHERE kingdom_id = :kid
            """
        ),
        {"kid": kingdom_id},
    ).fetchone()

    if not record:
        total_slots = 0
        used_slots = 0
    else:
        (
            base,
            build_bonus,
            tech_bonus,
            project_bonus,
            event_bonus,
            used_slots,
        ) = record
        total_slots = base + build_bonus + tech_bonus + project_bonus + event_bonus

    if used_slots + troops_requested > total_slots:
        raise HTTPException(status_code=400, detail="Not enough troop slots")


def _merge_modifiers(target: dict, new_mods: dict) -> None:
    """Helper to merge modifier dictionaries into the target structure."""
    if not isinstance(new_mods, dict):
        return

    for category, values in new_mods.items():
        if not isinstance(values, dict):
            continue
        bucket = target.setdefault(category, {})
        for key, value in values.items():
            bucket[key] = bucket.get(key, 0) + value


def get_total_modifiers(db: Session, kingdom_id: int) -> dict:
    """Return the combined modifiers for a kingdom.

    The function aggregates modifiers from completed techs, active temples,
    active projects and region bonuses. Missing tables or columns are ignored so
    the function can operate in minimal database setups.
    """

    total = {
        "resource_bonus": {},
        "troop_bonus": {},
        "combat_bonus": {},
        "defense_bonus": {},
        "economic_bonus": {},
        "production_bonus": {},
    }

    # Region bonuses -----------------------------------------------------
    try:
        region_row = db.execute(
            text("SELECT region FROM kingdoms WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
        if region_row:
            region_data = db.execute(
                text(
                    "SELECT resource_bonus, troop_bonus FROM region_catalogue "
                    "WHERE region_code = :code"
                ),
                {"code": region_row[0]},
            ).fetchone()
            if region_data:
                resources, troop = region_data
                _merge_modifiers(
                    total,
                    {
                        "resource_bonus": resources or {},
                        "troop_bonus": troop or {},
                    },
                )
    except Exception as exc:
        logging.warning("Failed to apply region modifiers: %s", exc)

    # Completed techs ---------------------------------------------------
    try:
        rows = db.execute(
            text(
                "SELECT tc.modifiers FROM kingdom_research_tracking krt "
                "JOIN tech_catalogue tc ON tc.tech_code = krt.tech_code "
                "WHERE krt.kingdom_id = :kid AND krt.status = 'completed'"
            ),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as exc:
        logging.warning("Failed to apply completed tech modifiers: %s", exc)

    # Active temples ----------------------------------------------------
    try:
        rows = db.execute(
            text(
                "SELECT bc.modifiers FROM village_buildings vb "
                "JOIN kingdom_villages kv ON kv.village_id = vb.village_id "
                "JOIN building_catalogue bc ON bc.building_id = vb.building_id "
                "WHERE kv.kingdom_id = :kid "
                "AND bc.production_type = 'temple' "
                "AND vb.construction_status = 'complete'"
            ),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as exc:
        logging.warning("Failed to apply temple modifiers: %s", exc)

    # Active kingdom projects ------------------------------------------
    try:
        rows = db.execute(
            text(
                "SELECT pc.modifiers FROM projects_player pp "
                "JOIN project_player_catalogue pc ON pc.project_code = pp.project_code "
                "WHERE pp.kingdom_id = :kid"
            ),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as exc:
        logging.warning("Failed to apply kingdom project modifiers: %s", exc)

    # Active alliance projects -----------------------------------------
    try:
        rows = db.execute(
            text(
                """
                SELECT pa.modifiers
                FROM projects_alliance pa
                WHERE pa.alliance_id IN (
                    SELECT alliance_id FROM alliance_members
                    WHERE user_id = (
                        SELECT user_id FROM kingdoms WHERE kingdom_id = :kid
                    )
                )
                  AND pa.is_active = true
                  AND pa.build_state = 'completed'
                """
            ),
            {"kid": kingdom_id},
        ).fetchall()
        for (mods,) in rows:
            _merge_modifiers(total, mods or {})
    except Exception as exc:
        logging.warning("Failed to apply alliance project modifiers: %s", exc)

    # VIP perks ---------------------------------------------------------
    try:
        level = vip_levels.get(str(kingdom_id), vip_levels.get(kingdom_id, 0))
        perks = global_game_settings.get("vip_perks", {}).get(level, {})
        _merge_modifiers(total, perks)
    except Exception as exc:
        logging.warning("Failed to apply VIP perks: %s", exc)

    # Prestige bonuses --------------------------------------------------
    try:
        score = prestige_scores.get(str(kingdom_id), prestige_scores.get(kingdom_id, 0))
        if score:
            _merge_modifiers(total, {"combat_bonus": {"prestige": score // 100}})
    except Exception as exc:
        logging.warning("Failed to apply prestige bonuses: %s", exc)

    # Village bonuses ---------------------------------------------------
    try:
        rows = db.execute(
            text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
        village_count = rows[0] if rows else 0
        if village_count:
            _merge_modifiers(total, {"production_bonus": {"villages": village_count}})
    except Exception as exc:
        logging.warning("Failed to apply village bonuses: %s", exc)

    # Treaty modifiers --------------------------------------------------
    try:
        for treaty in kingdom_treaties.get(kingdom_id, []):
            _merge_modifiers(total, treaty.get("modifiers", {}))
    except Exception as exc:
        logging.warning("Failed to apply treaty modifiers: %s", exc)

    # Spy effects -------------------------------------------------------
    try:
        spy = kingdom_spies.get(kingdom_id)
        if spy:
            _merge_modifiers(total, spy.get("modifiers", {}))
    except Exception as exc:
        logging.warning("Failed to apply spy effects: %s", exc)

    # Global modifiers --------------------------------------------------
    try:
        if global_game_settings.get("event_modifiers"):
            _merge_modifiers(total, global_game_settings["event_modifiers"])
    except Exception as exc:
        logging.warning("Failed to apply global modifiers: %s", exc)

    return total
