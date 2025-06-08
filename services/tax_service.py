from __future__ import annotations

"""Service functions for alliance tax collections."""

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def collect_alliance_tax(
    db: Session,
    alliance_id: int,
    user_id: str,
    resource_type: str,
    earned_amount: int,
    source: str,
    notes: str = "",
) -> int:
    """Apply alliance tax when a player gains resources.

    Returns the net amount the player should receive after tax. The function
    updates the alliance vault and logs the collection event.
    """

    rate_row = db.execute(
        text(
            "SELECT tax_rate_percent FROM alliance_tax_policies "
            "WHERE alliance_id = :aid "
            "AND resource_type = :res "
            "AND is_active = true"
        ),
        {"aid": alliance_id, "res": resource_type},
    ).fetchone()

    if not rate_row:
        return earned_amount

    tax_rate = rate_row[0] or 0
    if tax_rate <= 0:
        return earned_amount

    tax_amount = int(earned_amount * tax_rate / 100)
    if tax_amount <= 0:
        return earned_amount

    # Deposit tax into alliance vault
    db.execute(
        text(
            f"UPDATE alliance_vault SET {resource_type} = COALESCE({resource_type}, 0) + :amt "
            "WHERE alliance_id = :aid"
        ),
        {"amt": tax_amount, "aid": alliance_id},
    )

    # Log collection event
    db.execute(
        text(
            """
            INSERT INTO alliance_tax_collections (
                alliance_id, user_id, resource_type,
                amount_collected, source, notes
            ) VALUES (
                :aid, :uid, :res, :amt, :src, :note
            )
            """
        ),
        {
            "aid": alliance_id,
            "uid": user_id,
            "res": resource_type,
            "amt": tax_amount,
            "src": source,
            "note": notes,
        },
    )

    # Record in vault transaction log as a system deposit
    db.execute(
        text(
            """
            INSERT INTO alliance_vault_transaction_log (
                alliance_id, user_id, action, resource_type, amount, notes
            ) VALUES (
                :aid, NULL, 'deposit', :res, :amt, :note
            )
            """
        ),
        {
            "aid": alliance_id,
            "res": resource_type,
            "amt": tax_amount,
            "note": f"Auto tax collection from {user_id}" if not notes else notes,
        },
    )

    db.commit()

    return earned_amount - tax_amount
