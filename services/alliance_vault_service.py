# Project Name: Thronestead©
# File Name: alliance_vault_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""Service functions for managing alliance vault interactions."""

from __future__ import annotations

import logging
from typing import Optional

from .resource_service import validate_resource

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # fallback for test environments

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Vault Core Interactions
# ------------------------------------------------------------------------------


def get_vault_balance(db: Session, alliance_id: int) -> dict:
    """Return the current resource holdings of the alliance vault."""
    row = db.execute(
        text("SELECT * FROM alliance_vault WHERE alliance_id = :aid"),
        {"aid": alliance_id},
    ).fetchone()

    return dict(row._mapping) if row else {}


def deposit_to_vault(
    db: Session,
    alliance_id: int,
    user_id: Optional[str],
    resource_type: str,
    amount: int,
    notes: str = "manual deposit",
) -> None:
    """Deposit a resource into the alliance vault and log it."""
    validate_resource(resource_type)
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")

    # Ensure vault row exists
    db.execute(
        text(
            """
            INSERT INTO alliance_vault (alliance_id)
            VALUES (:aid)
            ON CONFLICT (alliance_id) DO NOTHING
        """
        ),
        {"aid": alliance_id},
    )

    # Apply the deposit
    db.execute(
        text(
            f"""
            UPDATE alliance_vault
            SET {resource_type} = COALESCE({resource_type}, 0) + :amt
            WHERE alliance_id = :aid
        """
        ),
        {"aid": alliance_id, "amt": amount},
    )

    # Log it
    db.execute(
        text(
            """
            INSERT INTO alliance_vault_transaction_log (
                alliance_id, user_id, action, resource_type, amount, notes
            ) VALUES (
                :aid, :uid, 'deposit', :res, :amt, :note
            )
        """
        ),
        {
            "aid": alliance_id,
            "uid": user_id,
            "res": resource_type,
            "amt": amount,
            "note": notes,
        },
    )

    db.commit()


def withdraw_from_vault(
    db: Session,
    alliance_id: int,
    user_id: Optional[str],
    resource_type: str,
    amount: int,
    notes: str = "manual withdrawal",
) -> None:
    """Withdraw resources from the alliance vault and log the transaction."""
    validate_resource(resource_type)
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive")

    # Check current balance
    current = db.execute(
        text(
            f"""
            SELECT COALESCE({resource_type}, 0)
            FROM alliance_vault
            WHERE alliance_id = :aid
        """
        ),
        {"aid": alliance_id},
    ).scalar()

    if current is None or current < amount:
        raise ValueError("Insufficient resources in vault")

    # Apply the withdrawal
    db.execute(
        text(
            f"""
            UPDATE alliance_vault
            SET {resource_type} = GREATEST(COALESCE({resource_type}, 0) - :amt, 0)
            WHERE alliance_id = :aid
        """
        ),
        {"aid": alliance_id, "amt": amount},
    )

    # Log the withdrawal
    db.execute(
        text(
            """
            INSERT INTO alliance_vault_transaction_log (
                alliance_id, user_id, action, resource_type, amount, notes
            ) VALUES (
                :aid, :uid, 'withdraw', :res, :amt, :note
            )
        """
        ),
        {
            "aid": alliance_id,
            "uid": user_id,
            "res": resource_type,
            "amt": amount,
            "note": notes,
        },
    )

    db.commit()


def get_transaction_log(
    db: Session,
    alliance_id: int,
    limit: int = 100,
) -> list[dict]:
    """Return recent vault transactions for the alliance."""
    rows = db.execute(
        text(
            """
            SELECT transaction_id, user_id, action, resource_type,
                   amount, notes, created_at
            FROM alliance_vault_transaction_log
            WHERE alliance_id = :aid
            ORDER BY created_at DESC
            LIMIT :lim
        """
        ),
        {"aid": alliance_id, "lim": limit},
    ).fetchall()

    return [dict(r._mapping) for r in rows]


def audit_vault(db: Session, alliance_id: int) -> dict:
    """Return a full snapshot of the vault state and recent activity."""
    return {
        "balance": get_vault_balance(db, alliance_id),
        "recent_transactions": get_transaction_log(db, alliance_id, limit=50),
    }
