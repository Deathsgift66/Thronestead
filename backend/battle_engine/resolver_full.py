# Project Name: Thronestead©
# File Name: resolver_full.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""Full combat resolver processing kingdom and alliance wars."""

import logging
from typing import Any, Dict, List

from ..db import db
from .movement import process_unit_movement
from .vision import process_unit_vision

logger = logging.getLogger("Thronestead.BattleEngine")


def process_unit_combat(
    unit: Dict[str, Any],
    all_units: List[Dict[str, Any]],
    terrain: List[List[str]],
    war_id: int,
    tick: int,
    war_type: str,
) -> None:
    """Resolve combat for ``unit`` against nearby enemies."""

    unit_id = unit["movement_id"]
    kingdom_id = unit["kingdom_id"]
    pos_x = unit["position_x"]
    pos_y = unit["position_y"]
    quantity = unit.get("quantity", 0)

    for other in all_units:
        if other["kingdom_id"] == kingdom_id:
            continue

        distance = max(
            abs(pos_x - other["position_x"]),
            abs(pos_y - other["position_y"]),
        )

        if distance > 1:
            continue

        casualties = min(quantity, other.get("quantity", 0))
        if casualties <= 0:
            continue

        remaining = max(0, other["quantity"] - casualties)
        other["quantity"] = remaining

        db.execute(
            """
            UPDATE unit_movements
            SET quantity = %s, status = CASE WHEN %s = 0 THEN 'defeated' ELSE status END
            WHERE movement_id = %s
            """,
            (remaining, remaining, other["movement_id"]),
        )

        if war_type == "alliance":
            db.execute(
                """
                INSERT INTO alliance_war_combat_logs (
                    alliance_war_id, tick_number, event_type, attacker_unit_id,
                    defender_unit_id, position_x, position_y, damage_dealt,
                    morale_shift, notes
                )
                VALUES (%s, %s, 'attack', %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    war_id,
                    tick,
                    unit_id,
                    other["movement_id"],
                    other["position_x"],
                    other["position_y"],
                    casualties,
                    0.0,
                    "alliance",
                ),
            )
        else:
            db.execute(
                """
                INSERT INTO combat_logs (
                    war_id, tick_number, event_type, attacker_unit_id,
                    defender_unit_id, position_x, position_y, damage_dealt,
                    morale_shift, notes
                )
                VALUES (%s, %s, 'attack', %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    war_id,
                    tick,
                    unit_id,
                    other["movement_id"],
                    other["position_x"],
                    other["position_y"],
                    casualties,
                    0.0,
                    war_type,
                ),
            )


# ============================================
# COMBAT RESOLVER — FULL ENGINE SKELETON
# ============================================


def run_combat_tick() -> None:
    """Process one combat tick for all active wars."""

    # --- Process Kingdom Wars ---
    active_kingdom_wars = db.query(
        """
        SELECT war_id, phase, castle_hp, battle_tick, weather
        FROM wars_tactical
        WHERE phase = 'battle' AND war_status = 'active'
        """
    )

    for war in active_kingdom_wars:
        process_kingdom_war_tick(war)

    # --- Process Alliance Wars ---
    active_alliance_wars = db.query(
        """
        SELECT alliance_war_id, phase, castle_hp, battle_tick, weather
        FROM alliance_wars
        WHERE phase = 'battle' AND war_status = 'active'
        """
    )

    for awar in active_alliance_wars:
        process_alliance_war_tick(awar)


# ============================================
# PROCESS KINGDOM WAR TICK
# ============================================


def process_kingdom_war_tick(war: Dict[str, Any]) -> None:
    """Advance a single tick for a kingdom vs. kingdom war."""
    war_id = war["war_id"]
    tick = war["battle_tick"] + 1
    weather = war.get("weather")

    logger.info("Processing Kingdom War ID %s — Tick %s", war_id, tick)

    units = db.query(
        """
        SELECT um.*, us.speed, us."class", us.can_build_bridge
        FROM unit_movements AS um
        JOIN unit_stats AS us ON um.unit_type = us.unit_type
        WHERE um.war_id = %s AND um.status = 'active'
        """,
        (war_id,),
    )

    terrain = db.query(
        """
        SELECT tile_map FROM terrain_map
        WHERE war_id = %s
        """,
        (war_id,),
    ).first()["tile_map"]

    # --- MAIN LOOP ---
    for unit in units:
        process_unit_movement(unit, terrain, weather)
        process_unit_vision(unit, units, terrain, weather)
        process_unit_combat(unit, units, terrain, war_id, tick, "kingdom")

    # --- UPDATE TICK ---
    db.execute(
        """
        UPDATE wars_tactical
        SET battle_tick = %s
        WHERE war_id = %s
        """,
        (tick, war_id),
    )

    # --- CHECK VICTORY ---
    check_victory_condition_kingdom(war_id)


# ============================================
# PROCESS ALLIANCE WAR TICK
# ============================================


def process_alliance_war_tick(awar: Dict[str, Any]) -> None:
    """Advance a single tick for an alliance war."""
    alliance_war_id = awar["alliance_war_id"]
    tick = awar["battle_tick"] + 1
    weather = awar.get("weather")

    logger.info("Processing Alliance War ID %s — Tick %s", alliance_war_id, tick)

    participants = db.query(
        """
        SELECT kingdom_id FROM alliance_war_participants
        WHERE alliance_war_id = %s
        """,
        (alliance_war_id,),
    )

    participant_kingdom_ids = [p["kingdom_id"] for p in participants]

    units = db.query(
        """
        SELECT um.*, us.speed, us."class", us.can_build_bridge
        FROM unit_movements AS um
        JOIN unit_stats AS us ON um.unit_type = us.unit_type
        WHERE um.kingdom_id = ANY(%s) AND um.war_id IS NULL
          AND um.status = 'active'
        """,
        (participant_kingdom_ids,),
    )

    terrain = db.query(
        """
        SELECT tile_map FROM terrain_map
        WHERE war_id = %s
        """,
        (alliance_war_id,),
    ).first()["tile_map"]

    # --- MAIN LOOP ---
    for unit in units:
        process_unit_movement(unit, terrain, weather)
        process_unit_vision(unit, units, terrain, weather)
        process_unit_combat(unit, units, terrain, alliance_war_id, tick, "alliance")

    # --- UPDATE TICK ---
    db.execute(
        """
        UPDATE alliance_wars
        SET battle_tick = %s
        WHERE alliance_war_id = %s
        """,
        (tick, alliance_war_id),
    )

    update_alliance_war_score(alliance_war_id)

    # --- CHECK VICTORY ---
    check_victory_condition_alliance(alliance_war_id)


def update_alliance_war_score(alliance_war_id: int) -> None:
    """Update attacker and defender scores for the given alliance war."""

    awar = db.query(
        """
        SELECT castle_hp FROM alliance_wars
        WHERE alliance_war_id = %s
        """,
        (alliance_war_id,),
    ).first()

    if not awar:
        return

    attacker_score = 10000 - awar["castle_hp"]
    defender_score = awar["castle_hp"]

    db.execute(
        """
        INSERT INTO alliance_war_scores (alliance_war_id, attacker_score, defender_score)
        VALUES (%s, %s, %s)
        ON CONFLICT (alliance_war_id) DO UPDATE
        SET attacker_score = %s, defender_score = %s, last_updated = now()
        """,
        (
            alliance_war_id,
            attacker_score,
            defender_score,
            attacker_score,
            defender_score,
        ),
    )


# ============================================
# CHECK VICTORY — KINGDOM WAR
# ============================================


def check_victory_condition_kingdom(war_id: int) -> None:
    war = db.query(
        """
        SELECT castle_hp, battle_tick FROM wars_tactical
        WHERE war_id = %s
        """,
        (war_id,),
    ).first()

    if war["castle_hp"] <= 0:
        logger.info("Kingdom War %s — ATTACKER WINS!", war_id)
        db.execute(
            """
            UPDATE wars_tactical SET war_status = 'completed'
            WHERE war_id = %s
            """,
            (war_id,),
        )
        db.execute(
            """
            INSERT INTO war_scores (war_id, victor) VALUES (%s, 'attacker')
            """,
            (war_id,),
        )
        att_cas, def_cas = calculate_kingdom_war_casualties(war_id)
        insert_battle_resolution_log(
            "kingdom",
            war_id,
            None,
            "attacker",
            war["battle_tick"],
            att_cas,
            def_cas,
            {},
            0,
            None,
        )

    elif war["battle_tick"] >= 12:
        logger.info("Kingdom War %s — BATTLE ENDED AT TICK 12", war_id)
        victor = determine_victor(war_id)
        db.execute(
            """
            UPDATE wars_tactical SET war_status = 'completed'
            WHERE war_id = %s
            """,
            (war_id,),
        )
        db.execute(
            """
            INSERT INTO war_scores (war_id, victor) VALUES (%s, %s)
            """,
            (war_id, victor),
        )
        att_cas, def_cas = calculate_kingdom_war_casualties(war_id)
        insert_battle_resolution_log(
            "kingdom",
            war_id,
            None,
            victor,
            war["battle_tick"],
            att_cas,
            def_cas,
            {},
            0,
            None,
        )


# ============================================
# CHECK VICTORY — ALLIANCE WAR
# ============================================


def check_victory_condition_alliance(alliance_war_id: int) -> None:
    awar = db.query(
        """
        SELECT castle_hp, battle_tick FROM alliance_wars
        WHERE alliance_war_id = %s
        """,
        (alliance_war_id,),
    ).first()

    if awar["castle_hp"] <= 0:
        logger.info("Alliance War %s — ATTACKER WINS!", alliance_war_id)
        db.execute(
            """
            UPDATE alliance_wars SET war_status = 'completed'
            WHERE alliance_war_id = %s
            """,
            (alliance_war_id,),
        )
        db.execute(
            """
            INSERT INTO alliance_war_scores (alliance_war_id, victor)
            VALUES (%s, 'attacker')
            ON CONFLICT (alliance_war_id) DO UPDATE
            SET victor = 'attacker', last_updated = now()
            """,
            (alliance_war_id,),
        )
        att_cas, def_cas = calculate_alliance_war_casualties(alliance_war_id)
        insert_battle_resolution_log(
            "alliance",
            None,
            alliance_war_id,
            "attacker",
            awar["battle_tick"],
            att_cas,
            def_cas,
            {},
            0,
            None,
        )

    elif awar["battle_tick"] >= 12:
        logger.info("Alliance War %s — BATTLE ENDED AT TICK 12", alliance_war_id)
        victor = determine_victor_alliance(alliance_war_id)
        db.execute(
            """
            UPDATE alliance_wars SET war_status = 'completed'
            WHERE alliance_war_id = %s
            """,
            (alliance_war_id,),
        )
        db.execute(
            """
            INSERT INTO alliance_war_scores (alliance_war_id, victor)
            VALUES (%s, %s)
            ON CONFLICT (alliance_war_id) DO UPDATE
            SET victor = %s, last_updated = now()
            """,
            (alliance_war_id, victor, victor),
        )
        att_cas, def_cas = calculate_alliance_war_casualties(alliance_war_id)
        insert_battle_resolution_log(
            "alliance",
            None,
            alliance_war_id,
            victor,
            awar["battle_tick"],
            att_cas,
            def_cas,
            {},
            0,
            None,
        )


# ============================================
# DETERMINE VICTOR — EXAMPLE LOGIC
# ============================================


def determine_victor(war_id: int) -> str:
    war = db.query(
        "SELECT castle_hp FROM wars_tactical WHERE war_id = %s",
        (war_id,),
    ).first()
    if war["castle_hp"] > 500:
        return "defender"
    return "attacker"


def determine_victor_alliance(alliance_war_id: int) -> str:
    awar = db.query(
        "SELECT castle_hp FROM alliance_wars WHERE alliance_war_id = %s",
        (alliance_war_id,),
    ).first()
    if awar["castle_hp"] > 500:
        return "defender"
    return "attacker"


def calculate_kingdom_war_casualties(war_id: int) -> tuple[int, int]:
    """Return attacker and defender casualties for ``war_id``."""

    info = db.query(
        """
        SELECT attacker_kingdom_id, defender_kingdom_id
        FROM wars_tactical
        WHERE war_id = %s
        """,
        (war_id,),
    ).first()

    if not info:
        return 0, 0

    attacker_id = info["attacker_kingdom_id"]
    defender_id = info["defender_kingdom_id"]

    att_row = db.query(
        """
        SELECT COALESCE(SUM(cl.damage_dealt), 0) AS dmg
        FROM combat_logs cl
        JOIN unit_movements um ON cl.defender_unit_id = um.movement_id
        WHERE cl.war_id = %s AND um.kingdom_id = %s
        """,
        (war_id, attacker_id),
    ).first()

    def_row = db.query(
        """
        SELECT COALESCE(SUM(cl.damage_dealt), 0) AS dmg
        FROM combat_logs cl
        JOIN unit_movements um ON cl.defender_unit_id = um.movement_id
        WHERE cl.war_id = %s AND um.kingdom_id = %s
        """,
        (war_id, defender_id),
    ).first()

    att_cas = att_row["dmg"] if att_row else 0
    def_cas = def_row["dmg"] if def_row else 0
    return int(att_cas or 0), int(def_cas or 0)


def calculate_alliance_war_casualties(alliance_war_id: int) -> tuple[int, int]:
    """Return attacker and defender casualties for an alliance war."""

    attackers = db.query(
        """
        SELECT kingdom_id FROM alliance_war_participants
        WHERE alliance_war_id = %s AND role = 'attacker'
        """,
        (alliance_war_id,),
    )
    defenders = db.query(
        """
        SELECT kingdom_id FROM alliance_war_participants
        WHERE alliance_war_id = %s AND role = 'defender'
        """,
        (alliance_war_id,),
    )

    attacker_ids = [r["kingdom_id"] for r in attackers]
    defender_ids = [r["kingdom_id"] for r in defenders]

    att_row = db.query(
        """
        SELECT COALESCE(SUM(l.damage_dealt), 0) AS dmg
        FROM alliance_war_combat_logs l
        JOIN unit_movements um ON l.defender_unit_id = um.movement_id
        WHERE l.alliance_war_id = %s AND um.kingdom_id = ANY(%s)
        """,
        (alliance_war_id, attacker_ids),
    ).first()

    def_row = db.query(
        """
        SELECT COALESCE(SUM(l.damage_dealt), 0) AS dmg
        FROM alliance_war_combat_logs l
        JOIN unit_movements um ON l.defender_unit_id = um.movement_id
        WHERE l.alliance_war_id = %s AND um.kingdom_id = ANY(%s)
        """,
        (alliance_war_id, defender_ids),
    ).first()

    att_total = int(att_row["dmg"] if att_row else 0)
    def_total = int(def_row["dmg"] if def_row else 0)

    return att_total, def_total


# ============================================
# INSERT BATTLE RESOLUTION LOG
# ============================================


def insert_battle_resolution_log(
    battle_type: str,
    war_id: int | None,
    alliance_war_id: int | None,
    victor: str,
    total_ticks: int,
    attacker_casualties: int = 0,
    defender_casualties: int = 0,
    loot_summary: dict | None = None,
    gold_looted: int = 0,
    resources_looted: str | None = None,
) -> None:
    """Persist final battle outcome in ``battle_resolution_logs``."""

    loot_json = loot_summary or {}

    logger.info(
        "Inserting Battle Resolution Log — %s WAR — Victor: %s",
        battle_type.upper(),
        victor,
    )

    db.execute(
        """
        INSERT INTO battle_resolution_logs (
            battle_type,
            war_id,
            alliance_war_id,
            winner_side,
            total_ticks,
            attacker_casualties,
            defender_casualties,
            loot_summary,
            gold_looted,
            resources_looted
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            battle_type,
            war_id,
            alliance_war_id,
            victor,
            total_ticks,
            attacker_casualties,
            defender_casualties,
            loot_json,
            gold_looted,
            resources_looted,
        ),
    )
