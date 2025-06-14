# Project Name: Kingmakers Rise©
# File Name: combat_log_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""Service functions for logging and retrieving combat log data."""

from __future__ import annotations
from datetime import datetime
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def log_combat_event(
    db: Session,
    war_id: int,
    tick: int,
    acting_unit_id: int,
    target_unit_id: int,
    action_type: str,
    result_summary: str,
    damage: int = 0,
    morale_shift: int = 0,
    terrain_effect: str | None = None,
    weather_effect: str | None = None,
    special_notes: str | None = None,
) -> int:
    """
    Logs a single combat event in the combat log table.
    Returns the inserted log_id.
    """
    result = db.execute(
        text(
            """
            INSERT INTO combat_logs (
                war_id, tick, acting_unit_id, target_unit_id, action_type,
                result_summary, damage, morale_shift, terrain_effect, weather_effect,
                special_notes, occurred_at
            ) VALUES (
                :war_id, :tick, :acting_uid, :target_uid, :atype,
                :summary, :dmg, :morale, :terrain, :weather,
                :notes, NOW()
            ) RETURNING log_id
            """
        ),
        {
            "war_id": war_id,
            "tick": tick,
            "acting_uid": acting_unit_id,
            "target_uid": target_unit_id,
            "atype": action_type,
            "summary": result_summary,
            "dmg": damage,
            "morale": morale_shift,
            "terrain": terrain_effect,
            "weather": weather_effect,
            "notes": special_notes,
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
            SELECT log_id, tick, acting_unit_id, target_unit_id,
                   action_type, result_summary, damage, morale_shift,
                   terrain_effect, weather_effect, special_notes, occurred_at
            FROM combat_logs
            WHERE war_id = :wid
            ORDER BY tick ASC, log_id ASC
            LIMIT :lim
            """
        ),
        {"wid": war_id, "lim": limit},
    ).fetchall()

    return [
        {
            "log_id": r[0],
            "tick": r[1],
            "acting_unit_id": r[2],
            "target_unit_id": r[3],
            "action_type": r[4],
            "result_summary": r[5],
            "damage": r[6],
            "morale_shift": r[7],
            "terrain_effect": r[8],
            "weather_effect": r[9],
            "special_notes": r[10],
            "occurred_at": r[11],
        }
        for r in rows
    ]


def fetch_logs_by_tick(db: Session, war_id: int, tick: int) -> list[dict]:
    """
    Returns all combat events for a specific tick in a war.
    Useful for visual tick-based replay rendering.
    """
    rows = db.execute(
        text(
            """
            SELECT log_id, acting_unit_id, target_unit_id,
                   action_type, result_summary, damage, morale_shift,
                   terrain_effect, weather_effect, special_notes, occurred_at
            FROM combat_logs
            WHERE war_id = :wid AND tick = :tick
            ORDER BY log_id ASC
            """
        ),
        {"wid": war_id, "tick": tick},
    ).fetchall()

    return [
        {
            "log_id": r[0],
            "acting_unit_id": r[1],
            "target_unit_id": r[2],
            "action_type": r[3],
            "result_summary": r[4],
            "damage": r[5],
            "morale_shift": r[6],
            "terrain_effect": r[7],
            "weather_effect": r[8],
            "special_notes": r[9],
            "occurred_at": r[10],
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
                   SUM(damage) as total_damage,
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
