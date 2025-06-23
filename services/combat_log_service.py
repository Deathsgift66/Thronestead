# Project Name: Thronestead©
# File Name: combat_log_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""Service functions for logging and retrieving combat log data."""

from __future__ import annotations

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore


def log_combat_event(
    db: Session,
    war_id: int,
    tick_number: int,
    attacker_unit_id: int,
    defender_unit_id: int,
    event_type: str,
    damage_dealt: int = 0,
    morale_shift: float = 0.0,
    position_x: int | None = None,
    position_y: int | None = None,
    notes: str | None = None,
    treaty_trigger_context: dict | None = None,
    triggered_by_treaty: bool = False,
    treaty_name: str | None = None,
) -> int:
    """
    Logs a single combat event in the combat log table.
    Returns the inserted log_id.
    """
    result = db.execute(
        text(
            """
            INSERT INTO combat_logs (
                war_id, tick_number, event_type, attacker_unit_id,
                defender_unit_id, position_x, position_y, damage_dealt,
                morale_shift, notes, treaty_trigger_context, triggered_by_treaty,
                treaty_name, timestamp
            ) VALUES (
                :war_id, :tick_number, :event_type, :attacker_unit_id,
                :defender_unit_id, :position_x, :position_y, :damage_dealt,
                :morale_shift, :notes, :treaty_context, :triggered,
                :treaty_name, NOW()
            ) RETURNING combat_id
            """
        ),
        {
            "war_id": war_id,
            "tick_number": tick_number,
            "event_type": event_type,
            "attacker_unit_id": attacker_unit_id,
            "defender_unit_id": defender_unit_id,
            "position_x": position_x,
            "position_y": position_y,
            "damage_dealt": damage_dealt,
            "morale_shift": morale_shift,
            "notes": notes,
            "treaty_context": treaty_trigger_context or {},
            "triggered": triggered_by_treaty,
            "treaty_name": treaty_name,
        },
    )
    row = result.fetchone()
    db.commit()
    return row[0] if row else 0


def fetch_logs_for_war(db: Session, war_id: int, limit: int = 500) -> list[dict]:
    """
    Returns the latest combat logs for a given war.
    Includes tick info, unit IDs, and full summary details.
    """
    rows = db.execute(
        text(
            """
            SELECT combat_id, tick_number, event_type, attacker_unit_id,
                   defender_unit_id, position_x, position_y, damage_dealt,
                   morale_shift, notes, timestamp,
                   treaty_trigger_context, triggered_by_treaty, treaty_name
            FROM combat_logs
            WHERE war_id = :wid
            ORDER BY tick_number ASC, combat_id ASC
            LIMIT :lim
            """
        ),
        {"wid": war_id, "lim": limit},
    ).fetchall()

    return [
        {
            "combat_id": r[0],
            "tick_number": r[1],
            "event_type": r[2],
            "attacker_unit_id": r[3],
            "defender_unit_id": r[4],
            "position_x": r[5],
            "position_y": r[6],
            "damage_dealt": r[7],
            "morale_shift": r[8],
            "notes": r[9],
            "timestamp": r[10],
            "treaty_trigger_context": r[11],
            "triggered_by_treaty": r[12],
            "treaty_name": r[13],
        }
        for r in rows
    ]


def fetch_logs_by_tick(db: Session, war_id: int, tick_number: int) -> list[dict]:
    """
    Returns all combat events for a specific tick in a war.
    Useful for visual tick-based replay rendering.
    """
    rows = db.execute(
        text(
            """
            SELECT combat_id, attacker_unit_id, defender_unit_id,
                   event_type, damage_dealt, morale_shift, position_x,
                   position_y, notes, timestamp,
                   treaty_trigger_context, triggered_by_treaty, treaty_name
            FROM combat_logs
            WHERE war_id = :wid AND tick_number = :tick
            ORDER BY combat_id ASC
            """
        ),
        {"wid": war_id, "tick": tick_number},
    ).fetchall()

    return [
        {
            "combat_id": r[0],
            "attacker_unit_id": r[1],
            "defender_unit_id": r[2],
            "event_type": r[3],
            "damage_dealt": r[4],
            "morale_shift": r[5],
            "position_x": r[6],
            "position_y": r[7],
            "notes": r[8],
            "timestamp": r[9],
            "treaty_trigger_context": r[10],
            "triggered_by_treaty": r[11],
            "treaty_name": r[12],
        }
        for r in rows
    ]


def summarize_combat_outcome(db: Session, war_id: int) -> dict:
    """
    Summarizes damage dealt, morale impact, and actions performed in the war.
    Useful for post-battle statistics and resolution UI.
    """
    result = db.execute(
        text(
            """
            SELECT COUNT(*) as total_events,
                   SUM(damage_dealt) as total_damage,
                   SUM(morale_shift) as total_morale_shift
            FROM combat_logs
            WHERE war_id = :wid
            """
        ),
        {"wid": war_id},
    ).fetchone()

    return {
        "total_events": result[0] or 0,
        "total_damage": result[1] or 0,
        "total_morale_shift": result[2] or 0,
    }
