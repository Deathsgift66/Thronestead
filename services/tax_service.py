# Project Name: Thronestead©
# File Name: tax_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Service functions for alliance tax collections.

from __future__ import annotations

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Alliance Tax Processing
# ------------------------------------------------------------


def collect_alliance_tax(
    db: Session,
    alliance_id: int,
    user_id: str,
    resource_type: str,
    earned_amount: int,
    source: str,
    notes: str = "",
) -> int:
    """
    Calculate and deduct alliance tax from player-earned resources.

    Args:
        db: Database session
        alliance_id: ID of the alliance
        user_id: UUID of the player
        resource_type: e.g., 'gold', 'wood'
        earned_amount: Full amount earned by the player
        source: Source system triggering the tax (e.g., 'quest_reward')
        notes: Optional description of the context

    Returns:
        int: Net amount after tax deduction (to be credited to the player)
    """
    try:
        # Step 1: Fetch tax rate
        rate_row = db.execute(
            text(
                """
                SELECT tax_rate_percent
                  FROM alliance_tax_policies
                 WHERE alliance_id = :aid
                   AND resource_type = :res
                   AND is_active = true
            """
            ),
            {"aid": alliance_id, "res": resource_type},
        ).fetchone()

        if not rate_row:
            return earned_amount

        tax_rate = rate_row[0] or 0
        if tax_rate <= 0:
            return earned_amount

        # Step 2: Calculate tax amount
        tax_amount = int(earned_amount * tax_rate / 100)
        if tax_amount <= 0:
            return earned_amount

        # Step 3: Update alliance vault balance
        db.execute(
            text(
                f"""
                UPDATE alliance_vault
                   SET {resource_type} = COALESCE({resource_type}, 0) + :amt
                 WHERE alliance_id = :aid
            """
            ),
            {"amt": tax_amount, "aid": alliance_id},
        )

        # Step 4: Log tax collection
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

        # Step 5: Log to alliance vault transaction log
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

        # Return the net result
        return earned_amount - tax_amount

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Alliance tax collection failed for %s", resource_type)
        return earned_amount
