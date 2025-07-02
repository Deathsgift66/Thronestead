# Project Name: Thronestead©
# File Name: war_battle_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""Service logic for executing and resolving live tactical war battles."""

from __future__ import annotations

import logging

from services.sqlalchemy_support import Session, text

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Main Tick Processor
# ------------------------------------------------------------------------------


def process_battle_tick(db: Session, war_id: int) -> dict:
    """Advance battle state by one tick and return outcome summary."""
    # Ensure war is active
    status = db.execute(
        text("SELECT status FROM wars WHERE war_id = :wid"),
        {"wid": war_id},
    ).scalar()
    if status != "active":
        raise ValueError("Battle is not active")

    # Get current tick
    tick = db.execute(
        text("SELECT current_tick FROM war_tick_state WHERE war_id = :wid"),
        {"wid": war_id},
    ).scalar()

    if tick is None:
        raise ValueError("Tick state not initialized")

    new_tick = tick + 1

    # 1. Process Orders
    process_orders(db, war_id, new_tick)

    # 2. Resolve Combat
    resolve_combat(db, war_id, new_tick)

    # 3. Update Positions (movement)
    update_positions(db, war_id, new_tick)

    # 4. Apply Morale Loss / Unit Fatigue
    apply_morale_penalties(db, war_id, new_tick)

    # 5. Log Tick Summary
    log_battle_tick(db, war_id, new_tick)

    # 6. Update Tick State
    db.execute(
        text("UPDATE war_tick_state SET current_tick = :t WHERE war_id = :wid"),
        {"t": new_tick, "wid": war_id},
    )

    db.commit()

    # 7. If max tick, conclude battle
    if new_tick >= 12:
        conclude_battle(db, war_id)
        return {"status": "concluded", "tick": new_tick}

    return {"status": "active", "tick": new_tick}


# ------------------------------------------------------------------------------
# Helper Actions
# ------------------------------------------------------------------------------


def process_orders(db: Session, war_id: int, tick: int) -> None:
    """Read and apply player-issued orders (stance, fallback, patrol, etc)."""
    db.execute(
        text(
            """
            UPDATE unit_orders
            SET applied_tick = :tick
            WHERE war_id = :wid AND applied_tick IS NULL
        """
        ),
        {"tick": tick, "wid": war_id},
    )


def resolve_combat(db: Session, war_id: int, tick: int) -> None:
    """Simulate combat between opposing units in same tile."""
    db.execute(
        text(
            """
            INSERT INTO combat_logs (war_id, tick, attacker_unit_id, defender_unit_id, outcome)
            SELECT :wid, :tick, a.unit_id, b.unit_id,
                   CASE WHEN a.power > b.defense THEN 'win' ELSE 'loss' END
            FROM unit_positions a
            JOIN unit_positions b
              ON a.x = b.x AND a.y = b.y
             AND a.alliance_id != b.alliance_id
            WHERE a.war_id = :wid AND b.war_id = :wid
        """
        ),
        {"wid": war_id, "tick": tick},
    )


def update_positions(db: Session, war_id: int, tick: int) -> None:
    """Move units based on movement orders."""
    db.execute(
        text(
            """
            UPDATE unit_positions
            SET x = x + dx, y = y + dy, last_moved_tick = :tick
            FROM unit_movements
            WHERE unit_positions.unit_id = unit_movements.unit_id
              AND unit_positions.war_id = :wid
              AND unit_movements.war_id = :wid
        """
        ),
        {"tick": tick, "wid": war_id},
    )


def apply_morale_penalties(db: Session, war_id: int, tick: int) -> None:
    """Reduce morale for routed, isolated, or under-fire units."""
    db.execute(
        text(
            """
            UPDATE unit_positions
            SET morale = GREATEST(morale - 10, 0)
            WHERE war_id = :wid
              AND morale > 0
              AND unit_id IN (
                  SELECT unit_id FROM combat_logs
                  WHERE war_id = :wid AND tick = :tick AND outcome = 'loss'
              )
        """
        ),
        {"wid": war_id, "tick": tick},
    )


def log_battle_tick(db: Session, war_id: int, tick: int) -> None:
    """Create a summary tick log for replay/resolution."""
    db.execute(
        text(
            """
            INSERT INTO war_tick_logs (war_id, tick, created_at)
            VALUES (:wid, :tick, now())
        """
        ),
        {"wid": war_id, "tick": tick},
    )


# ------------------------------------------------------------------------------
# Battle Conclusion
# ------------------------------------------------------------------------------


def conclude_battle(db: Session, war_id: int) -> None:
    """Finalize battle, calculate final score, set war to concluded."""
    # Calculate score
    db.execute(
        text(
            """
            INSERT INTO war_results (war_id, final_tick, attacker_score, defender_score)
            SELECT :wid, 12,
                (SELECT COUNT(*) FROM unit_positions WHERE war_id = :wid AND is_attacker = TRUE),
                (SELECT COUNT(*) FROM unit_positions WHERE war_id = :wid AND is_attacker = FALSE)
        """
        ),
        {"wid": war_id},
    )

    ids_row = db.execute(
        text(
            "SELECT attacker_kingdom_id, defender_kingdom_id FROM wars WHERE war_id = :wid"
        ),
        {"wid": war_id},
    ).fetchone()

    # Set war as concluded
    db.execute(
        text(
            "UPDATE wars SET status = 'concluded', end_date = now() WHERE war_id = :wid"
        ),
        {"wid": war_id},
    )

    if ids_row:
        attacker_id, defender_id = ids_row
        if attacker_id:
            db.execute(
                text(
                    "UPDATE kingdom_troop_slots SET currently_in_combat = false WHERE kingdom_id = :kid"
                ),
                {"kid": attacker_id},
            )
        if defender_id:
            db.execute(
                text(
                    "UPDATE kingdom_troop_slots SET currently_in_combat = false WHERE kingdom_id = :kid"
                ),
                {"kid": defender_id},
            )

    # Apply morale adjustments based on the outcome
    try:
        from services.combat_log_service import apply_war_outcome_morale

        apply_war_outcome_morale(db, war_id)
    except Exception as e:  # pragma: no cover - log but don't block conclusion
        logger.debug("Morale update failed: %s", e)

    db.commit()
    logger.info(f"War {war_id} concluded at tick 12.")


# ------------------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------------------


def fetch_battle_state(db: Session, war_id: int) -> dict:
    """Return the latest snapshot of a battle's current state."""
    tick = (
        db.execute(
            text("SELECT current_tick FROM war_tick_state WHERE war_id = :wid"),
            {"wid": war_id},
        ).scalar()
        or 0
    )

    units = db.execute(
        text(
            """
            SELECT unit_id, x, y, morale, alliance_id
            FROM unit_positions
            WHERE war_id = :wid
        """
        ),
        {"wid": war_id},
    ).fetchall()

    return {
        "tick": tick,
        "units": [dict(r._mapping) for r in units],
    }
