# Project Name: Thronestead©
# File Name: strategic_tick_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Automation helpers for periodic game state updates (strategic tick).

from __future__ import annotations

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object

# External tick-participating modules
from services.kingdom_quest_service import expire_quests

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Utility: Central Logging + Notifications
# ------------------------------------------------------------


def _log_unified(db: Session, event_type: str, details: str) -> None:
    """
    Writes a unified event log entry (if table is enabled).
    """
    try:
        db.execute(
            text("INSERT INTO unified_logs (event_type, details) VALUES (:et, :de)"),
            {"et": event_type, "de": details},
        )
    except Exception as e:
        logger.debug("Unified log unavailable: %s", e)


def _notify_event(db: Session, event_type: str, ref_id: int, info: str = "") -> None:
    """
    Fires a system event notification (if table is enabled).
    """
    try:
        db.execute(
            text(
                """
                INSERT INTO event_notification_log (event_type, reference_id, info)
                VALUES (:et, :rid, :info)
            """
            ),
            {"et": event_type, "rid": ref_id, "info": info},
        )
    except Exception as e:
        logger.debug("Event notification log unavailable: %s", e)


# ------------------------------------------------------------
# Core Tick Modules
# ------------------------------------------------------------


def update_project_progress(db: Session) -> int:
    """
    Marks completed alliance projects that have reached their end time.

    Returns:
        int: number of completed projects
    """
    result = db.execute(
        text(
            """
            UPDATE projects_alliance_in_progress
               SET status = 'completed', last_updated = now()
             WHERE status = 'building' AND expected_end <= now()
        """
        )
    )
    db.commit()
    count = getattr(result, "rowcount", 0)
    if count:
        _log_unified(db, "project_completed", f"{count} alliance projects completed")
    return count


def update_quest_progress(db: Session) -> int:
    """
    Completes fully-progressed quests and expires overdue ones.

    Returns:
        int: total number of affected quests
    """
    completed = db.execute(
        text(
            """
            UPDATE quest_kingdom_tracking
               SET status = 'completed',
                   is_complete = true,
                   last_updated = now()
             WHERE status = 'active' AND progress >= 100
        """
        )
    )
    expired = expire_quests(db)
    db.commit()

    done = getattr(completed, "rowcount", 0)
    if done:
        _log_unified(db, "quest_completed", f"{done} quests completed")
    return done + expired


def expire_treaties(db: Session) -> int:
    """Cancel long-running treaties based on their signing date."""

    res_a = db.execute(
        text(
            """
            UPDATE alliance_treaties

               SET status = 'expired'
             WHERE status = 'active' AND signed_at < now() - interval '30 days'

            """
        )
    )
    res_k = db.execute(
        text(
            """
            UPDATE kingdom_treaties

               SET status = 'expired'
             WHERE status = 'active' AND signed_at < now() - interval '30 days'

            """
        )
    )
    db.commit()
    count = (getattr(res_a, "rowcount", 0) or 0) + (getattr(res_k, "rowcount", 0) or 0)
    if count:
        _log_unified(db, "treaties_expired", f"{count} treaties expired")
    return count


def activate_pending_wars(db: Session) -> int:
    """
    Activates wars whose start time has passed.

    Returns:
        int: number of wars activated
    """
    rows = db.execute(
        text(
            """
            UPDATE wars
               SET status='active'
             WHERE status = 'pending' AND start_date <= now()
             RETURNING war_id, attacker_kingdom_id, defender_kingdom_id
        """
        )
    ).fetchall()

    for _, atk, defn in rows:
        if atk:
            db.execute(
                text(
                    """
                    UPDATE kingdom_troop_slots
                       SET currently_in_combat = true,
                           last_in_combat_at = now()
                     WHERE kingdom_id = :kid
                    """
                ),
                {"kid": atk},
            )
        if defn:
            db.execute(
                text(
                    """
                    UPDATE kingdom_troop_slots
                       SET currently_in_combat = true,
                           last_in_combat_at = now()
                     WHERE kingdom_id = :kid
                    """
                ),
                {"kid": defn},
            )

    db.commit()
    war_ids = [r[0] for r in rows]

    for wid in war_ids:
        _notify_event(db, "new_war", wid)

    if war_ids:
        _log_unified(db, "wars_activated", f"{len(war_ids)} wars activated")

    return len(war_ids)


def check_war_status(db: Session) -> int:
    """
    Concludes wars that have reached their end date.

    Returns:
        int: number of wars concluded
    """
    res_k = db.execute(
        text(
            "UPDATE wars SET status='concluded' WHERE status = 'active' AND end_date < now()"
        )
    )
    res_a = db.execute(
        text(
            "UPDATE alliance_wars SET war_status='concluded' WHERE war_status = 'active' AND end_date < now()"
        )
    )
    db.commit()
    count = (getattr(res_k, "rowcount", 0) or 0) + (getattr(res_a, "rowcount", 0) or 0)
    if count:
        _log_unified(db, "wars_concluded", f"{count} wars concluded")
    return count


def restore_kingdom_morale(db: Session) -> int:
    """Gradually restore troop morale for all kingdoms."""
    result = db.execute(
        text(
            """
            UPDATE kingdom_troop_slots
               SET morale = LEAST(
                       100,
                       morale
                           + 5
                           + morale_bonus_buildings
                           + morale_bonus_tech
                           + morale_bonus_events
                   ),
                   last_morale_update = now()
             WHERE morale < 100
               AND (
                       morale_cooldown_seconds <= 0
                    OR last_morale_update + morale_cooldown_seconds * interval '1 second' <= now()
               )
            """
        )
    )
    db.commit()
    count = getattr(result, "rowcount", 0)
    if count:
        _log_unified(db, "morale_restored", f"{count} kingdoms morale restored")
    return count


def decrement_morale_cooldowns(db: Session, seconds: int = 60) -> int:
    """Reduce morale cooldown timers for all kingdoms."""
    result = db.execute(
        text(
            """
            UPDATE kingdom_troop_slots
               SET morale_cooldown_seconds = GREATEST(0, morale_cooldown_seconds - :sec)
             WHERE morale_cooldown_seconds > 0
            """
        ),
        {"sec": seconds},
    )
    db.commit()
    return getattr(result, "rowcount", 0)


# ------------------------------------------------------------
# Strategic Tick Executor
# ------------------------------------------------------------


def process_tick(db: Session) -> None:
    """
    Executes the full strategic tick for the game.

    Includes:
    - Project completions
    - Quest completions/expirations
    - Treaty expirations
    - War activations and resolutions
    """
    try:
        results = {
            "projects": update_project_progress(db),
            "quests": update_quest_progress(db),
            "treaties": expire_treaties(db),
            "wars_started": activate_pending_wars(db),
            "wars_concluded": check_war_status(db),
            "morale_cooldown": decrement_morale_cooldowns(db),
            "morale_restored": restore_kingdom_morale(db),
        }
        logger.info("[Strategic Tick] %s", results)
    except Exception as e:
        logger.exception("Tick processing failed: %s", e)
