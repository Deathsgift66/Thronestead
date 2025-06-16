# Project Name: Kingmakers Rise©
# File Name: spies_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Database helpers for kingdom spy management system.

import logging
from typing import Optional

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover
    def text(q):  # type: ignore
        return q

    Session = object

logger = logging.getLogger(__name__)

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
        row = db.execute(
            text("SELECT * FROM kingdom_spies WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()

        if not row:
            db.execute(
                text("INSERT INTO kingdom_spies (kingdom_id) VALUES (:kid)"),
                {"kid": kingdom_id},
            )
            db.commit()
            row = db.execute(
                text("SELECT * FROM kingdom_spies WHERE kingdom_id = :kid"),
                {"kid": kingdom_id},
            ).fetchone()

        return dict(row._mapping)

    except SQLAlchemyError as e:
        logger.exception("Failed to retrieve or create spy record for kingdom %d", kingdom_id)
        raise RuntimeError("Spy record retrieval failed") from e


def train_spies(db: Session, kingdom_id: int, quantity: int) -> int:
    """
    Trains spies, up to the max capacity.

    Returns:
        int: new total spy count
    """
    record = get_spy_record(db, kingdom_id)
    new_count = min(record.get("spy_count", 0) + quantity, record.get("max_spy_capacity", 0))

    db.execute(
        text("""
            UPDATE kingdom_spies
               SET spy_count = :cnt,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
        """),
        {"cnt": new_count, "kid": kingdom_id},
    )
    db.commit()
    return new_count

# ------------------------------------------------------------
# Spy Mission Lifecycle
# ------------------------------------------------------------

def start_mission(db: Session, kingdom_id: int, cooldown: int = 3600) -> None:
    """
    Starts a spy mission and sets the cooldown timer.

    Args:
        cooldown (int): seconds to wait before next mission
    """
    db.execute(
        text("""
            UPDATE kingdom_spies
               SET last_mission_at = NOW(),
                   cooldown_seconds = :cool,
                   missions_attempted = missions_attempted + 1,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
        """),
        {"cool": cooldown, "kid": kingdom_id},
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
        text("""
            UPDATE kingdom_spies
               SET spy_count = GREATEST(spy_count - :loss, 0),
                   spies_lost = spies_lost + :loss,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
        """),
        {"loss": loss, "kid": kingdom_id},
    )
    db.commit()

# ------------------------------------------------------------
# Spy Missions Table
# ------------------------------------------------------------

def create_spy_mission(
    db: Session,
    kingdom_id: int,
    mission_type: str,
    target_id: Optional[int] = None
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
        text("""
            INSERT INTO spy_missions (kingdom_id, mission_type, target_id, status)
            VALUES (:kid, :type, :tid, 'active')
            RETURNING mission_id
        """),
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
        text("""
            SELECT mission_id, kingdom_id, mission_type, target_id, status,
                   launched_at, completed_at
              FROM spy_missions
             WHERE kingdom_id = :kid
             ORDER BY launched_at DESC
             LIMIT :lim
        """),
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
        text("""
            UPDATE spy_missions
               SET status = :st,
                   completed_at = NOW()
             WHERE mission_id = :mid
        """),
        {"st": status, "mid": mission_id},
    )
    db.commit()
