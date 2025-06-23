# Project Name: Thronestead©
# File Name: alliance_treaty_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66
# Description: Alliance-level treaty logic — proposal, acceptance, cancellation, and listing.

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ----------------------------
# Treaty Service Functions
# ----------------------------


def propose_treaty(
    db: Session,
    alliance_id: int,
    partner_alliance_id: int,
    treaty_type: str,
) -> None:
    """
    Propose a new treaty between two alliances.
    Ensures no active treaty of this type exists between them before inserting.
    """
    try:
        exists = db.execute(
            text(
                """
                SELECT 1 FROM alliance_treaties
                 WHERE ((alliance_id = :aid AND partner_alliance_id = :pid)
                        OR (alliance_id = :pid AND partner_alliance_id = :aid))
                   AND treaty_type = :type
                   AND status = 'active'
            """
            ),
            {"aid": alliance_id, "pid": partner_alliance_id, "type": treaty_type},
        ).fetchone()

        if exists:
            raise ValueError(
                "An active treaty of this type already exists between the two alliances."
            )

        db.execute(
            text(
                """
                INSERT INTO alliance_treaties (alliance_id, partner_alliance_id, treaty_type, status)
                VALUES (:aid, :pid, :type, 'proposed')
            """
            ),
            {"aid": alliance_id, "pid": partner_alliance_id, "type": treaty_type},
        )
        db.commit()

    except SQLAlchemyError as e:
        logger.exception("Failed to propose treaty")
        db.rollback()
        raise RuntimeError("Database error occurred while proposing treaty") from e


def accept_treaty(db: Session, treaty_id: int) -> None:
    """
    Accept a treaty proposal, changing its status to 'active' and setting the signed timestamp.
    """
    try:
        db.execute(
            text(
                """
                UPDATE alliance_treaties
                   SET status = 'active', signed_at = now()
                 WHERE treaty_id = :tid
            """
            ),
            {"tid": treaty_id},
        )
        db.commit()

    except SQLAlchemyError as e:
        logger.exception("Failed to accept treaty")
        db.rollback()
        raise RuntimeError("Database error occurred while accepting treaty") from e


def cancel_treaty(db: Session, treaty_id: int) -> None:
    """
    Cancel an active or proposed treaty. Updates the status and signed_at timestamp.
    """
    try:
        db.execute(
            text(
                """
                UPDATE alliance_treaties
                   SET status = 'cancelled', signed_at = now()
                 WHERE treaty_id = :tid
            """
            ),
            {"tid": treaty_id},
        )
        db.commit()

    except SQLAlchemyError as e:
        logger.exception("Failed to cancel treaty")
        db.rollback()
        raise RuntimeError("Database error occurred while cancelling treaty") from e


def list_active_treaties(db: Session, alliance_id: int) -> list[dict]:
    """
    List all active treaties involving the specified alliance (as initiator or partner).
    """
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at
              FROM alliance_treaties
             WHERE (alliance_id = :aid OR partner_alliance_id = :aid)
               AND status = 'active'
             ORDER BY signed_at DESC
        """
        ),
        {"aid": alliance_id},
    ).fetchall()

    return [_map_treaty_row(r) for r in rows]


def list_incoming_proposals(db: Session, alliance_id: int) -> list[dict]:
    """
    List treaties proposed to the specified alliance.
    """
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at
              FROM alliance_treaties
             WHERE partner_alliance_id = :aid
               AND status = 'proposed'
             ORDER BY treaty_id DESC
        """
        ),
        {"aid": alliance_id},
    ).fetchall()

    return [_map_treaty_row(r) for r in rows]


def list_outgoing_proposals(db: Session, alliance_id: int) -> list[dict]:
    """
    List treaty proposals sent by the specified alliance.
    """
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at
              FROM alliance_treaties
             WHERE alliance_id = :aid
               AND status = 'proposed'
             ORDER BY treaty_id DESC
        """
        ),
        {"aid": alliance_id},
    ).fetchall()

    return [_map_treaty_row(r) for r in rows]


# ----------------------------
# Internal Utility
# ----------------------------


def _map_treaty_row(row) -> dict:
    """Convert DB row into a dictionary for frontend consumption."""
    return {
        "treaty_id": row[0],
        "alliance_id": row[1],
        "treaty_type": row[2],
        "partner_alliance_id": row[3],
        "status": row[4],
        "signed_at": row[5],
    }
