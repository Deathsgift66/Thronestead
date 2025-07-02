from __future__ import annotations

import logging

from services.sqlalchemy_support import Session, text

logger = logging.getLogger(__name__)


def process_combat_tick(db: Session, war_id: int, tick_number: int, payload: dict) -> bool:
    """Apply a single combat tick ensuring backup and idempotency."""
    db.execute(
        text(
            """
            INSERT INTO combat_tick_queue_backup (war_id, tick_number, payload)
            VALUES (:wid, :tick, :payload)
            """
        ),
        {"wid": war_id, "tick": tick_number, "payload": payload},
    )

    try:
        db.execute(
            text(
                """
                INSERT INTO tick_execution_log (war_id, tick_number)
                VALUES (:wid, :tick)
                """
            ),
            {"wid": war_id, "tick": tick_number},
        )
    except Exception:  # pragma: no cover - treat as duplicate
        db.rollback()
        return False

    db.execute(
        text(
            """
            UPDATE wars_tactical
               SET battle_tick = :tick,
                   last_tick_processed_at = now()
             WHERE war_id = :wid
            """
        ),
        {"tick": tick_number, "wid": war_id},
    )
    db.commit()
    return True


def watchdog_restart(db: Session, delay_seconds: int = 300) -> int:
    """Requeue ticks for wars with stalled processing."""
    rows = db.execute(
        text(
            """
            SELECT war_id, battle_tick
              FROM wars_tactical
             WHERE war_status = 'active'
               AND now() - last_tick_processed_at > (:sec * interval '1 second')
            """
        ),
        {"sec": delay_seconds},
    ).fetchall()

    for wid, tick in rows:
        process_combat_tick(db, wid, tick + 1, {"auto_restart": True})

    return len(rows)
