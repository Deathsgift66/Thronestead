# Project Name: Thronestead©
# File Name: spies_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
# Description: Database helpers for kingdom spy management system.

import logging
import datetime
from typing import Optional

from services import resource_service
from services.constants import XP_PER_LEVEL

from services.sqlalchemy_support import Session, SQLAlchemyError, text

logger = logging.getLogger(__name__)

# Cost and scaling constants
SPY_TRAIN_COST_GOLD = 250
UPKEEP_PER_SPY = 1


# ------------------------------------------------------------
# Spy Record Management
# ------------------------------------------------------------


def get_spy_record(db: Session, kingdom_id: int) -> dict:
    """
    Retrieve the spy record for a kingdom.
    Creates a new row if one does not exist.

    Returns:
        dict: spy stats row for the kingdom
    """
    try:
        # Try to insert and return the row in one round trip. If the row
        # already exists the insert will be ignored and ``row`` will be ``None``.
        row = db.execute(
            text(
                """
                INSERT INTO kingdom_spies (kingdom_id)
                VALUES (:kid)
                ON CONFLICT (kingdom_id) DO NOTHING
                RETURNING *
                """
            ),
            {"kid": kingdom_id},
        ).fetchone()

        if not row:
            row = db.execute(
                text("SELECT * FROM kingdom_spies WHERE kingdom_id = :kid"),
                {"kid": kingdom_id},
            ).fetchone()

        return dict(row._mapping)

    except SQLAlchemyError as e:
        logger.exception(
            "Failed to retrieve or create spy record for kingdom %d", kingdom_id
        )
        raise RuntimeError("Spy record retrieval failed") from e


def train_spies(db: Session, kingdom_id: int, quantity: int) -> int:
    """
    Trains spies, up to the max capacity.

    Returns:
        int: new total spy count
    """
    record = get_spy_record(db, kingdom_id)
    capacity = record.get("max_spy_capacity", 0)
    current = record.get("spy_count", 0)
    if current + quantity > capacity:
        raise ValueError("Spy capacity reached")
    trainable = min(quantity, capacity - current)
    if trainable <= 0:
        return current

    total_cost = SPY_TRAIN_COST_GOLD * trainable
    # Deduct gold using centralized resource helper
    resource_service.spend_resources(db, kingdom_id, {"gold": total_cost}, commit=False)

    new_count = current + trainable
    xp_gain = trainable * 5
    new_xp = (record.get("spy_xp", 0) or 0) + xp_gain
    upkeep_gain = trainable * UPKEEP_PER_SPY
    new_upkeep = (record.get("spy_upkeep_gold", 0) or 0) + upkeep_gain
    new_level = 1 + new_xp // XP_PER_LEVEL

    db.execute(
        text(
            """
            UPDATE kingdom_spies
               SET spy_count = :cnt,
                   spy_xp = :xp,
                   spy_upkeep_gold = :upkeep,
                   spy_level = :lvl,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
        """
        ),
        {
            "cnt": new_count,
            "xp": new_xp,
            "upkeep": new_upkeep,
            "lvl": new_level,
            "kid": kingdom_id,
        },
    )
    db.commit()
    return new_count


# ------------------------------------------------------------
# Spy Mission Lifecycle
# ------------------------------------------------------------


def can_launch_mission(db: Session, kingdom_id: int) -> bool:
    """Return True if the kingdom's spy mission cooldown has elapsed."""

    try:
        row = db.execute(
            text(
                """
                SELECT last_mission_at, cooldown_seconds
                  FROM kingdom_spies
                 WHERE kingdom_id = :kid
                """
            ),
            {"kid": kingdom_id},
        ).fetchone()

        if not row:
            return True

        last_time = row[0]
        cooldown = row[1] or 0

        if last_time is None:
            return True

        now = datetime.datetime.now(datetime.timezone.utc)
        return last_time + datetime.timedelta(seconds=cooldown) <= now

    except SQLAlchemyError:
        logger.exception(
            "Failed to check spy mission cooldown for kingdom %d", kingdom_id
        )
        return False


def start_mission(
    db: Session,
    kingdom_id: int,
    target_id: Optional[int] = None,
    cooldown: int = 3600,
) -> None:
    """Starts a spy mission, updating cooldown and daily counters."""

    if target_id is None:
        raise ValueError("target_id is required")

    if not can_launch_mission(db, kingdom_id):
        raise ValueError("Mission still on cooldown")

    db.execute(
        text(
            """
            UPDATE kingdom_spies
               SET last_mission_at = NOW(),
                   cooldown_seconds = :cool,
                   missions_attempted = missions_attempted + 1,
                   daily_attacks_sent = daily_attacks_sent + 1,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
            """
        ),
        {"cool": cooldown, "kid": kingdom_id},
    )
    if target_id is not None:
        db.execute(
            text(
                """
                UPDATE kingdom_spies
                   SET daily_attacks_received = daily_attacks_received + 1,
                       last_updated = NOW()
                 WHERE kingdom_id = :tid
                """
            ),
            {"tid": target_id},
        )
    db.commit()


def record_success(db: Session, kingdom_id: int) -> None:
    """
    Increments the successful mission count.
    """
    db.execute(
        text(
            """
            UPDATE kingdom_spies
               SET missions_successful = missions_successful + 1,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
            """
        ),
        {"kid": kingdom_id},
    )
    db.commit()


def record_losses(db: Session, kingdom_id: int, loss: int) -> None:
    """
    Reduces spy count and tracks number of spies lost.

    Args:
        loss (int): number of spies lost
    """
    db.execute(
        text(
            """
            UPDATE kingdom_spies
               SET spy_count = GREATEST(spy_count - :loss, 0),
                   spies_lost = spies_lost + :loss,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
        """
        ),
        {"loss": loss, "kid": kingdom_id},
    )
    db.commit()


# ------------------------------------------------------------
# Spy Defense
# ------------------------------------------------------------


def get_spy_defense(db: Session, kingdom_id: int) -> int:
    """Return the espionage defense rating for a kingdom."""
    try:
        row = db.execute(
            text("SELECT defense_rating FROM spy_defense WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
        return int(row[0]) if row else 0
    except SQLAlchemyError:
        logger.exception("Failed to fetch spy defense for kingdom %d", kingdom_id)
        return 0


# ------------------------------------------------------------
# Spy Missions Table
# ------------------------------------------------------------


def create_spy_mission(
    db: Session, kingdom_id: int, mission_type: str, target_id: Optional[int] = None
) -> int:
    """
    Creates a new spy mission and returns its mission_id.

    Args:
        mission_type (str): mission type enum string
        target_id (Optional[int]): target kingdom or object ID

    Returns:
        int: new mission ID
    """
    row = db.execute(
        text(
            """
            INSERT INTO spy_missions (kingdom_id, mission_type, target_id, status)
            VALUES (:kid, :type, :tid, 'active')
            RETURNING mission_id
        """
        ),
        {"kid": kingdom_id, "type": mission_type, "tid": target_id},
    ).fetchone()
    db.commit()
    return int(row[0])


def list_spy_missions(db: Session, kingdom_id: int, limit: int = 50) -> list[dict]:
    """
    Lists recent spy missions for a kingdom.

    Returns:
        list of dicts containing mission info
    """
    rows = db.execute(
        text(
            """
            SELECT mission_id, kingdom_id, mission_type, target_id, status,
                   launched_at, completed_at
              FROM spy_missions
             WHERE kingdom_id = :kid
             ORDER BY launched_at DESC
             LIMIT :lim
        """
        ),
        {"kid": kingdom_id, "lim": limit},
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def update_mission_status(db: Session, mission_id: int, status: str) -> None:
    """
    Updates the status of a spy mission.

    Args:
        status (str): must be one of 'success', 'fail', 'cancelled', etc.
    """
    db.execute(
        text(
            """
            UPDATE spy_missions
               SET status = :st,
                   completed_at = NOW()
             WHERE mission_id = :mid
        """
        ),
        {"st": status, "mid": mission_id},
    )
    db.commit()


def finalize_mission(
    db: Session,
    mission_id: int,
    *,
    accuracy: float,
    detected: bool,
    spies_killed: int,
) -> None:
    """Set final mission details like accuracy and detection."""

    db.execute(
        text(
            """
            UPDATE spy_missions
               SET accuracy_percent = :acc,
                   was_detected = :det,
                   spies_killed = :loss
             WHERE mission_id = :mid
            """
        ),
        {
            "acc": accuracy,
            "det": detected,
            "loss": spies_killed,
            "mid": mission_id,
        },
    )
    db.commit()


def reset_daily_attack_counts(db: Session) -> int:
    """Reset daily spy attack counters for all kingdoms."""
    result = db.execute(
        text(
            """
            UPDATE kingdom_spies
               SET daily_attacks_sent = 0,
                   daily_attacks_received = 0,
                   last_updated = NOW()
            """
        )
    )
    db.commit()
    return getattr(result, "rowcount", 0)
