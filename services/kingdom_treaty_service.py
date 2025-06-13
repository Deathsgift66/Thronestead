import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def propose_treaty(
    db: Session,
    kingdom_id: int,
    partner_kingdom_id: int,
    treaty_type: str,
) -> None:
    """Insert a proposed treaty if no active treaty of the same type exists."""
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
        raise ValueError("Active treaty already exists")

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


def accept_treaty(db: Session, treaty_id: int) -> None:
    """Set a treaty to active and record the timestamp."""
    db.execute(
        text(
            "UPDATE kingdom_treaties SET status = 'active', signed_at = now() WHERE treaty_id = :tid"
        ),
        {"tid": treaty_id},
    )
    db.commit()


def cancel_treaty(db: Session, treaty_id: int) -> None:
    """Cancel a treaty."""
    db.execute(
        text(
            "UPDATE kingdom_treaties SET status = 'cancelled', signed_at = now() WHERE treaty_id = :tid"
        ),
        {"tid": treaty_id},
    )
    db.commit()


def list_active_treaties(db: Session, kingdom_id: int) -> list[dict]:
    """Return active treaties for the kingdom."""
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
    return [
        {
            "treaty_id": r[0],
            "kingdom_id": r[1],
            "treaty_type": r[2],
            "partner_kingdom_id": r[3],
            "status": r[4],
            "signed_at": r[5],
        }
        for r in rows
    ]


def list_incoming_proposals(db: Session, kingdom_id: int) -> list[dict]:
    """Return treaties proposed to the kingdom."""
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
    return [
        {
            "treaty_id": r[0],
            "kingdom_id": r[1],
            "treaty_type": r[2],
            "partner_kingdom_id": r[3],
            "status": r[4],
            "signed_at": r[5],
        }
        for r in rows
    ]


def list_outgoing_proposals(db: Session, kingdom_id: int) -> list[dict]:
    """Return treaties this kingdom has proposed."""
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
    return [
        {
            "treaty_id": r[0],
            "kingdom_id": r[1],
            "treaty_type": r[2],
            "partner_kingdom_id": r[3],
            "status": r[4],
            "signed_at": r[5],
        }
        for r in rows
    ]

