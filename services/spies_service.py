# Project Name: Kingmakers Rise©
# File Name: spies_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""Database helpers for kingdom spy management."""

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def get_spy_record(db: Session, kingdom_id: int) -> dict:
    """Fetch or initialize spy info for a kingdom."""
    row = db.execute(
        text("SELECT * FROM kingdom_spies WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    if not row:
        db.execute(
            text(
                """
                INSERT INTO kingdom_spies (kingdom_id)
                VALUES (:kid)
                """
            ),
            {"kid": kingdom_id},
        )
        db.commit()
        row = db.execute(
            text("SELECT * FROM kingdom_spies WHERE kingdom_id = :kid"),
            {"kid": kingdom_id},
        ).fetchone()
    return dict(row._mapping)


def train_spies(db: Session, kingdom_id: int, quantity: int) -> int:
    """Increase spy count respecting max capacity."""
    record = get_spy_record(db, kingdom_id)
    new_count = min(record.get("spy_count", 0) + quantity, record.get("max_spy_capacity", 0))
    db.execute(
        text(
            "UPDATE kingdom_spies SET spy_count = :cnt, last_updated = NOW() WHERE kingdom_id = :kid"
        ),
        {"cnt": new_count, "kid": kingdom_id},
    )
    db.commit()
    return new_count


def start_mission(db: Session, kingdom_id: int, cooldown: int = 3600) -> None:
    """Record mission start for a kingdom."""
    db.execute(
        text(
            """
            UPDATE kingdom_spies
               SET last_mission_at = NOW(),
                   cooldown_seconds = :cool,
                   missions_attempted = missions_attempted + 1,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
            """
        ),
        {"cool": cooldown, "kid": kingdom_id},
    )
    db.commit()


def record_success(db: Session, kingdom_id: int, xp_reward: int) -> None:
    """Update spy stats on mission success."""
    db.execute(
        text(
            """
            UPDATE kingdom_spies
               SET missions_successful = missions_successful + 1,
                   spy_xp = spy_xp + :xp,
                   last_updated = NOW()
             WHERE kingdom_id = :kid
            """
        ),
        {"xp": xp_reward, "kid": kingdom_id},
    )
    db.commit()


def record_losses(db: Session, kingdom_id: int, loss: int) -> None:
    """Decrease spy count and track losses."""
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


def create_spy_mission(
    db: Session, kingdom_id: int, mission_type: str, target_id: int | None
) -> int:
    """Insert a new spy mission row and return its ID."""
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
    """Return recent spy missions for a kingdom."""
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
    """Mark a mission complete with the given status."""
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
