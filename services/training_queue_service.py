# Project Name: Thronestead©
# File Name: training_queue_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Handles adding, updating, and viewing training queue entries for troops.

from __future__ import annotations

import logging
from typing import Optional

import datetime
from fastapi import HTTPException

from services.training_history_service import record_training
from services import resource_service
from services import kingdom_history_service

try:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Training Queue Service Functions
# ------------------------------------------------------------


def add_training_order(
    db: Session,
    kingdom_id: int,
    unit_id: int,
    unit_name: str,
    quantity: int,
    base_training_seconds: int,
    training_speed_modifier: float = 1.0,
    training_speed_multiplier: float = 1.0,
    xp_per_unit: int = 0,
    modifiers_applied: Optional[dict] = None,
    initiated_by: Optional[str] = None,
    priority: int = 1,
) -> int:
    """Queue a new troop training order applying costs and cooldowns."""

    try:
        # Fetch base unit definition for costs and cooldowns
        unit_row = (
            db.execute(
                text(
                    "SELECT training_time, tier, cooldown_seconds, "
                    "cost_wood, cost_stone, cost_gold, cost_food "
                    "FROM training_catalog WHERE unit_id = :uid"
                ),
                {"uid": unit_id},
            )
            .mappings()
            .fetchone()
        )

        if not unit_row:
            raise HTTPException(status_code=404, detail="Unit not found")

        cost = {}
        for res in ("wood", "stone", "gold", "food"):
            val = unit_row.get(f"cost_{res}") or 0
            if val:
                cost[res] = int(val) * quantity

        try:
            resource_service.spend_resources(db, kingdom_id, cost, commit=False)
        except HTTPException as exc:
            kingdom_history_service.log_event(
                db, kingdom_id, "training_order", "rejected_insufficient_resources"
            )
            raise

        # Determine building speed bonus
        b_row = db.execute(
            text(
                """
                SELECT bt.speed_multiplier
                  FROM village_buildings vb
                  JOIN kingdom_villages kv ON vb.village_id = kv.village_id
                  JOIN building_catalogue bc ON vb.building_id = bc.building_id
                  JOIN building_tiers bt ON bt.building_id = vb.building_id
                                         AND bt.level = vb.level
                 WHERE kv.kingdom_id = :kid
                   AND bc.production_type = 'training'
                   AND vb.construction_status = 'complete'
                 ORDER BY vb.level DESC
                 LIMIT 1
                """
            ),
            {"kid": kingdom_id},
        ).fetchone()

        building_multiplier = float(b_row[0]) if b_row else 1.0

        base_seconds = unit_row.get("training_time", base_training_seconds)
        total_seconds = (
            base_seconds
            * quantity
            * training_speed_modifier
            / (training_speed_multiplier * building_multiplier)
        )

        # Enforce cooldown based on most recent training
        cooldown = int(unit_row.get("cooldown_seconds") or 0)
        if cooldown > 0:
            last_row = db.execute(
                text(
                    """
                    SELECT completed_at FROM training_history
                     WHERE kingdom_id = :kid AND unit_id = :uid
                     ORDER BY completed_at DESC LIMIT 1
                    """
                ),
                {"kid": kingdom_id, "uid": unit_id},
            ).fetchone()

            if last_row and last_row[0]:
                last_time = last_row[0]
                if isinstance(last_time, str):
                    last_time = datetime.datetime.fromisoformat(last_time)
                if last_time + datetime.timedelta(seconds=cooldown) > datetime.datetime.now(datetime.timezone.utc):
                    kingdom_history_service.log_event(
                        db, kingdom_id, "training_order", "rejected_cooldown"
                    )
                    raise HTTPException(status_code=400, detail="Training cooldown active")

        result = db.execute(
            text(
                """
                INSERT INTO training_queue (
                    kingdom_id, unit_id, unit_name, quantity,
                    training_ends_at, started_at, status,
                    training_speed_modifier, training_speed_multiplier,
                    xp_per_unit, modifiers_applied,
                    initiated_by, priority
                ) VALUES (
                    :kid, :uid, :uname, :qty,
                    now() + :secs * interval '1 second', now(), 'queued',
                    :speed, :mult,
                    :xp, :mods,
                    :init, :pri
                )
                RETURNING queue_id
                """
            ),
            {
                "kid": kingdom_id,
                "uid": unit_id,
                "uname": unit_name,
                "qty": quantity,
                "secs": total_seconds,
                "speed": training_speed_modifier,
                "mult": training_speed_multiplier,
                "xp": xp_per_unit,
                "mods": modifiers_applied or {},
                "init": initiated_by,
                "pri": priority,
            },
        )
        row = result.fetchone()
        kingdom_history_service.log_event(
            db,
            kingdom_id,
            "training_order",
            "queued_with_bonus" if training_speed_multiplier > 1 else "queued",
        )
        db.commit()
        return int(row[0]) if row else 0

    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to insert training queue entry for %s x%d", unit_name, quantity
        )
        return 0


def fetch_queue(db: Session, kingdom_id: int) -> list[dict]:
    """
    Fetch all active queue entries for a kingdom, ordered by priority and start time.

    Args:
        db: DB session
        kingdom_id: Kingdom whose queue is being requested

    Returns:
        List[dict]: List of queued or in-progress units
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT q.queue_id, q.unit_name, q.quantity, q.training_ends_at, q.status,
                       COALESCE(us.is_support, false) AS is_support,
                       COALESCE(us.is_siege, false) AS is_siege
                FROM training_queue q
                LEFT JOIN unit_stats us ON q.unit_name = us.unit_type
                WHERE q.kingdom_id = :kid
                  AND q.status IN ('queued', 'training')
                ORDER BY q.priority DESC, q.started_at ASC
                """
            ),
            {"kid": kingdom_id},
        ).fetchall()

        return [
            {
                "queue_id": r[0],
                "unit_name": r[1],
                "quantity": r[2],
                "training_ends_at": r[3],
                "status": r[4],
                "is_support": r[5],
                "is_siege": r[6],
            }
            for r in rows
        ]
    except SQLAlchemyError:
        logger.warning("Unable to fetch training queue for kingdom_id=%s", kingdom_id)
        return []


def cancel_training(db: Session, queue_id: int, kingdom_id: int) -> None:
    """
    Cancel a training order.

    Args:
        db: DB session
        queue_id: ID of the training queue row
        kingdom_id: Owner kingdom for validation
    """
    try:
        db.execute(
            text(
                """
                UPDATE training_queue
                SET status = 'cancelled', last_updated = now()
                WHERE queue_id = :qid AND kingdom_id = :kid
                """
            ),
            {"qid": queue_id, "kid": kingdom_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to cancel training for queue_id=%s", queue_id)


def mark_completed(db: Session, queue_id: int) -> None:
    """
    Mark a training entry as completed.

    Args:
        db: DB session
        queue_id: ID of the queue row to complete
    """
    try:
        row = db.execute(
            text(
                """
                SELECT kingdom_id, unit_id, unit_name, quantity,
                       started_at, initiated_by, modifiers_applied,
                       xp_per_unit, training_speed_multiplier
                  FROM training_queue
                 WHERE queue_id = :qid
                """
            ),
            {"qid": queue_id},
        ).fetchone()

        db.execute(
            text(
                """
                UPDATE training_queue
                   SET status = 'completed', last_updated = now()
                 WHERE queue_id = :qid
                """
            ),
            {"qid": queue_id},
        )

        if row:
            record_training(
                db,
                kingdom_id=row[0],
                unit_id=row[1],
                unit_name=row[2],
                quantity=row[3],
                source="training_queue",
                initiated_at=row[4],
                trained_by=row[5],
                modifiers_applied=row[6],
                xp_per_unit=row[7],
                speed_modifier=row[8],
            )

        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to mark queue_id=%s as completed", queue_id)



def begin_training(db: Session, queue_id: int, kingdom_id: int) -> None:
    """Set a queued order to 'training'."""
    try:
        db.execute(
            text(
                """
                UPDATE training_queue
                   SET status = 'training', last_updated = now()
                 WHERE queue_id = :qid AND kingdom_id = :kid
                """
            ),
            {"qid": queue_id, "kid": kingdom_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to start training for queue_id=%s", queue_id)


def pause_training(db: Session, queue_id: int, kingdom_id: int) -> None:
    """Pause an active training order."""
    try:
        db.execute(
            text(
                """
                UPDATE training_queue
                   SET status = 'paused', last_updated = now()
                 WHERE queue_id = :qid AND kingdom_id = :kid
                """
            ),
            {"qid": queue_id, "kid": kingdom_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to pause training for queue_id=%s", queue_id)

def finalize_completed_orders(db: Session) -> int:
    """Finalize finished training orders.

    Finds all queue rows where ``training_ends_at`` has passed and the status is
    either ``queued`` or ``training``. Each found row is marked completed,
    recorded in the training history and then removed from the queue.

    Args:
        db: Active database session

    Returns:
        int: Number of orders processed
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT queue_id, kingdom_id, unit_id, unit_name, quantity,
                       started_at, initiated_by, modifiers_applied, xp_per_unit
                  FROM training_queue
                 WHERE training_ends_at <= now()
                   AND status IN ('queued', 'training')
                """
            )
        ).fetchall()

        processed = 0
        for r in rows:
            qid, kid, uid, uname, qty, started_at, initiated_by, mods, xp = r
            mark_completed(db, qid)
            record_training(
                db,
                kingdom_id=kid,
                unit_id=uid,
                unit_name=uname,
                quantity=qty,
                source="training_queue",
                initiated_at=started_at,
                trained_by=initiated_by,
                modifiers_applied=mods,
                xp_per_unit=xp or 0,
            )
            db.execute(
                text("DELETE FROM training_queue WHERE queue_id = :qid"),
                {"qid": qid},
            )
            db.commit()
            processed += 1

        return processed

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to finalize completed training orders")
        return 0

