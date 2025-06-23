# Project Name: Thronestead©
# File Name: vip_status_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Handles VIP tier tracking, validation, and updates per user.

from __future__ import annotations
from datetime import datetime
import logging

try:
    from backend.data import vip_levels
except Exception:  # pragma: no cover - when backend.data not available
    vip_levels = {}

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover - SQLAlchemy fallback

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# VIP Services
# ------------------------------------------------------------


def upsert_vip_status(
    db: Session,
    user_id: str,
    vip_level: int,
    expires_at: datetime | None = None,
    founder: bool = False,
) -> None:
    """
    Insert or update VIP tier status for a user.

    Args:
        db: Active SQLAlchemy session
        user_id: User UUID
        vip_level: VIP tier (e.g., 1 or 2)
        expires_at: Optional expiration datetime
        founder: True for permanent founder-level VIP

    Returns:
        None
    """
    try:
        db.execute(
            text(
                """
                INSERT INTO kingdom_vip_status (user_id, vip_level, expires_at, founder)
                VALUES (:uid, :lvl, :exp, :founder)
                ON CONFLICT (user_id)
                DO UPDATE SET vip_level = EXCLUDED.vip_level,
                              expires_at = EXCLUDED.expires_at,
                              founder = EXCLUDED.founder
                """
            ),
            {
                "uid": user_id,
                "lvl": vip_level,
                "exp": expires_at,
                "founder": founder,
            },
        )
        db.commit()
        logger.info("Upserted VIP level %s for user %s", vip_level, user_id)
        vip_levels[str(user_id)] = vip_level

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to upsert VIP status for user_id=%s", user_id)
        raise


def get_vip_status(db: Session, user_id: str) -> dict | None:
    """
    Retrieve VIP status info for a user.

    Args:
        db: SQLAlchemy session
        user_id: UUID of user

    Returns:
        dict | None: VIP details (vip_level, expires_at, founder)
    """
    try:
        row = db.execute(
            text(
                "SELECT vip_level, expires_at, founder "
                "FROM kingdom_vip_status WHERE user_id = :uid"
            ),
            {"uid": user_id},
        ).fetchone()

        if not row:
            vip_levels.pop(str(user_id), None)
            return None

        vip_levels[str(user_id)] = row[0]
        return {
            "vip_level": row[0],
            "expires_at": row[1],
            "founder": row[2],
        }

    except SQLAlchemyError:
        logger.warning("Failed to fetch VIP status for user_id=%s", user_id)
        return None


def is_vip_active(record: dict | None) -> bool:
    """
    Determine if a user's VIP status is currently active.

    Args:
        record: VIP record from `get_vip_status`

    Returns:
        bool: True if active
    """
    if not record:
        return False

    if record.get("founder"):
        return True

    vip_level = record.get("vip_level", 0)
    expires = record.get("expires_at")

    return bool(vip_level and expires and expires > datetime.utcnow())
