# Project Name: Thronestead©
# File Name: kingdom_treaty_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
# Description: Handles treaty logic between individual kingdoms (propose, accept, cancel, list).

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ----------------------------
# Treaty Lifecycle Functions
# ----------------------------


def propose_treaty(
    db: Session,
    kingdom_id: int,
    partner_kingdom_id: int,
    treaty_type: str,
) -> None:
    """
    Propose a treaty between two kingdoms.
    Fails if an active treaty of the same type already exists.

    Raises:
        ValueError if a treaty is already active.
    """
    try:
        exists = db.execute(
            text(
                """
                SELECT 1 FROM kingdom_treaties
                 WHERE ((kingdom_id = :kid AND partner_kingdom_id = :pid)
                        OR (kingdom_id = :pid AND partner_kingdom_id = :kid))
                   AND treaty_type = :type
                   AND status = 'active'
            """
            ),
            {"kid": kingdom_id, "pid": partner_kingdom_id, "type": treaty_type},
        ).fetchone()

        if exists:
            raise ValueError("An active treaty of this type already exists.")

        db.execute(
            text(
                """
                INSERT INTO kingdom_treaties (kingdom_id, partner_kingdom_id, treaty_type, status)
                VALUES (:kid, :pid, :type, 'proposed')
            """
            ),
            {"kid": kingdom_id, "pid": partner_kingdom_id, "type": treaty_type},
        )
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to propose treaty")
        raise RuntimeError("Database error during treaty proposal") from exc


def accept_treaty(db: Session, treaty_id: int) -> None:
    """
    Accept a treaty proposal.

    Args:
        treaty_id: ID of the treaty to activate.
    """
    try:
        db.execute(
            text(
                """
                UPDATE kingdom_treaties
                   SET status = 'active', signed_at = now()
                 WHERE treaty_id = :tid
            """
            ),
            {"tid": treaty_id},
        )
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to accept treaty %d", treaty_id)
        raise RuntimeError("Failed to accept treaty") from exc


def cancel_treaty(db: Session, treaty_id: int) -> None:
    """
    Cancel an existing treaty.

    Args:
        treaty_id: ID of the treaty to cancel.
    """
    try:
        db.execute(
            text(
                """
                UPDATE kingdom_treaties
                   SET status = 'cancelled', signed_at = now()
                 WHERE treaty_id = :tid
            """
            ),
            {"tid": treaty_id},
        )
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to cancel treaty %d", treaty_id)
        raise RuntimeError("Failed to cancel treaty") from exc


# ----------------------------
# Treaty Listing Functions
# ----------------------------


def list_active_treaties(db: Session, kingdom_id: int) -> list[dict]:
    """
    List all active treaties for a given kingdom (incoming or outgoing).

    Returns:
        List of dictionaries with treaty metadata.
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT treaty_id, kingdom_id, treaty_type, partner_kingdom_id, status, signed_at
                  FROM kingdom_treaties
                 WHERE (kingdom_id = :kid OR partner_kingdom_id = :kid)
                   AND status = 'active'
                 ORDER BY signed_at DESC
            """
            ),
            {"kid": kingdom_id},
        ).fetchall()

        return [_map_treaty_row(r) for r in rows]

    except SQLAlchemyError:
        logger.exception("Failed to list active treaties for kingdom %d", kingdom_id)
        return []


def list_incoming_proposals(db: Session, kingdom_id: int) -> list[dict]:
    """
    List treaties proposed TO the kingdom.

    Returns:
        List of proposals where this kingdom is the recipient.
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT treaty_id, kingdom_id, treaty_type, partner_kingdom_id, status, signed_at
                  FROM kingdom_treaties
                 WHERE partner_kingdom_id = :kid AND status = 'proposed'
                 ORDER BY treaty_id DESC
            """
            ),
            {"kid": kingdom_id},
        ).fetchall()

        return [_map_treaty_row(r) for r in rows]

    except SQLAlchemyError:
        logger.exception("Failed to list incoming proposals for kingdom %d", kingdom_id)
        return []


def list_outgoing_proposals(db: Session, kingdom_id: int) -> list[dict]:
    """
    List treaties proposed BY the kingdom.

    Returns:
        List of proposals where this kingdom is the initiator.
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT treaty_id, kingdom_id, treaty_type, partner_kingdom_id, status, signed_at
                  FROM kingdom_treaties
                 WHERE kingdom_id = :kid AND status = 'proposed'
                 ORDER BY treaty_id DESC
            """
            ),
            {"kid": kingdom_id},
        ).fetchall()

        return [_map_treaty_row(r) for r in rows]

    except SQLAlchemyError:
        logger.exception("Failed to list outgoing proposals for kingdom %d", kingdom_id)
        return []


# ----------------------------
# Utility
# ----------------------------


def _map_treaty_row(row) -> dict:
    """Convert DB row to dict structure."""
    return {
        "treaty_id": row[0],
        "kingdom_id": row[1],
        "treaty_type": row[2],
        "partner_kingdom_id": row[3],
        "status": row[4],
        "signed_at": row[5],
    }
