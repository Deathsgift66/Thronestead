# Project Name: Kingmakers Rise©
# File Name: alliance_treaty_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def propose_treaty(
    db: Session,
    alliance_id: int,
    partner_alliance_id: int,
    treaty_type: str,
) -> None:
    """Insert a proposed treaty if no active treaty of the same type exists."""
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
        raise ValueError("Active treaty already exists")

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


def accept_treaty(db: Session, treaty_id: int) -> None:
    """Set a treaty to active and record the timestamp."""
    db.execute(
        text(
            "UPDATE alliance_treaties SET status = 'active', signed_at = now() WHERE treaty_id = :tid"
        ),
        {"tid": treaty_id},
    )
    db.commit()


def cancel_treaty(db: Session, treaty_id: int) -> None:
    """Cancel a treaty."""
    db.execute(
        text(
            "UPDATE alliance_treaties SET status = 'cancelled', signed_at = now() WHERE treaty_id = :tid"
        ),
        {"tid": treaty_id},
    )
    db.commit()


def list_active_treaties(db: Session, alliance_id: int) -> list[dict]:
    """Return active treaties for the alliance."""
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
    return [
        {
            "treaty_id": r[0],
            "alliance_id": r[1],
            "treaty_type": r[2],
            "partner_alliance_id": r[3],
            "status": r[4],
            "signed_at": r[5],
        }
        for r in rows
    ]


def list_incoming_proposals(db: Session, alliance_id: int) -> list[dict]:
    """Return treaties proposed to the alliance."""
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at
              FROM alliance_treaties
             WHERE partner_alliance_id = :aid AND status = 'proposed'
             ORDER BY treaty_id DESC
            """
        ),
        {"aid": alliance_id},
    ).fetchall()
    return [
        {
            "treaty_id": r[0],
            "alliance_id": r[1],
            "treaty_type": r[2],
            "partner_alliance_id": r[3],
            "status": r[4],
            "signed_at": r[5],
        }
        for r in rows
    ]


def list_outgoing_proposals(db: Session, alliance_id: int) -> list[dict]:
    """Return treaties this alliance has proposed."""
    rows = db.execute(
        text(
            """
            SELECT treaty_id, alliance_id, treaty_type, partner_alliance_id, status, signed_at
              FROM alliance_treaties
             WHERE alliance_id = :aid AND status = 'proposed'
             ORDER BY treaty_id DESC
            """
        ),
        {"aid": alliance_id},
    ).fetchall()
    return [
        {
            "treaty_id": r[0],
            "alliance_id": r[1],
            "treaty_type": r[2],
            "partner_alliance_id": r[3],
            "status": r[4],
            "signed_at": r[5],
        }
        for r in rows
    ]
