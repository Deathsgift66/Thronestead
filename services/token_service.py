# Project Name: Thronestead©
# File Name: token_service.py
# Version: 6.14.2025
# Developer: Codex
"""Utility functions for managing Black Market token balances."""

from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import text


def get_balance(db: Session, user_id: str) -> int:
    """Return current token balance for a user."""
    row = db.execute(
        text("SELECT tokens FROM user_tokens WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    return row[0] if row else 0


def add_tokens(db: Session, user_id: str, amount: int) -> None:
    """Add tokens to a user's balance."""
    db.execute(
        text(
            """
            INSERT INTO user_tokens (user_id, tokens)
            VALUES (:uid, :amt)
            ON CONFLICT (user_id)
            DO UPDATE SET tokens = user_tokens.tokens + EXCLUDED.tokens
            """
        ),
        {"uid": user_id, "amt": amount},
    )
    db.commit()


def consume_tokens(db: Session, user_id: str, amount: int) -> bool:
    """Consume tokens if available. Returns True if successful."""
    row = db.execute(
        text("SELECT tokens FROM user_tokens WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    current = row[0] if row else 0
    if current < amount:
        return False
    db.execute(
        text("UPDATE user_tokens SET tokens = tokens - :amt WHERE user_id = :uid"),
        {"amt": amount, "uid": user_id},
    )
    db.commit()
    return True
