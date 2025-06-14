# Project Name: Kingmakers Rise©
# File Name: resource_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66
"""Service logic for handling kingdom resource economy — gain, spend, validate."""

from __future__ import annotations
from typing import Literal, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Core Supported Resource Types (sync with DB ENUM or constants)
# ------------------------------------------------------------------------------

RESOURCE_TYPES = {
    "wood", "stone", "iron_ore", "gold", "food", "coal", "livestock", "clay", "flax",
    "tools", "wood_planks", "refined_stone", "iron_ingots", "charcoal", "leather",
    "arrows", "swords", "axes", "shields", "armour", "wagon", "siege_weapons",
    "jewelry", "spear", "horses", "pitchforks", "gems"
}

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def validate_resource(resource: str) -> None:
    """Ensure a resource type is recognized."""
    if resource not in RESOURCE_TYPES:
        raise ValueError(f"Invalid resource type: {resource}")

# ------------------------------------------------------------------------------
# Public Methods
# ------------------------------------------------------------------------------

def get_kingdom_resources(db: Session, kingdom_id: int) -> dict:
    """
    Return current resource values for a kingdom.
    """
    row = db.execute(
        text("SELECT * FROM kingdom_resources WHERE kingdom_id = :kid"),
        {"kid": kingdom_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Kingdom resource row missing.")

    return dict(row._mapping)


def spend_resources(db: Session, kingdom_id: int, cost: dict[str, int]) -> None:
    """
    Deduct specified resources from the kingdom.
    Will raise HTTPException if insufficient resources are available.
    """
    current = get_kingdom_resources(db, kingdom_id)

    for res, amt in cost.items():
        validate_resource(res)
        if amt < 0:
            raise ValueError("Negative spending not allowed")
        if current.get(res, 0) < amt:
            raise HTTPException(status_code=400, detail=f"Not enough {res}")

    set_clause = ", ".join([f"{r} = {r} - :{r}" for r in cost])
    sql = f"UPDATE kingdom_resources SET {set_clause} WHERE kingdom_id = :kid"

    db.execute(text(sql), {**cost, "kid": kingdom_id})
    db.commit()


def gain_resources(db: Session, kingdom_id: int, gain: dict[str, int]) -> None:
    """
    Add specified resources to the kingdom.
    """
    for res, amt in gain.items():
        validate_resource(res)
        if amt < 0:
            raise ValueError("Negative gain not allowed")

    set_clause = ", ".join([f"{r} = COALESCE({r}, 0) + :{r}" for r in gain])
    sql = f"UPDATE kingdom_resources SET {set_clause} WHERE kingdom_id = :kid"

    db.execute(text(sql), {**gain, "kid": kingdom_id})
    db.commit()


def has_enough_resources(db: Session, kingdom_id: int, cost: dict[str, int]) -> bool:
    """
    Return True if kingdom has all required resources.
    """
    current = get_kingdom_resources(db, kingdom_id)
    for res, amt in cost.items():
        validate_resource(res)
        if current.get(res, 0) < amt:
            return False
    return True


def transfer_resource(
    db: Session,
    from_kingdom_id: int,
    to_kingdom_id: int,
    resource: str,
    amount: int,
    reason: str = "",
    log: bool = True,
) -> None:
    """
    Transfer resources between kingdoms (e.g., gifting).
    """
    validate_resource(resource)
    if amount <= 0:
        raise ValueError("Transfer amount must be positive.")

    current = get_kingdom_resources(db, from_kingdom_id)
    if current.get(resource, 0) < amount:
        raise HTTPException(status_code=400, detail="Not enough resources to transfer.")

    # Spend from sender
    spend_resources(db, from_kingdom_id, {resource: amount})
    # Give to recipient
    gain_resources(db, to_kingdom_id, {resource: amount})

    if log:
        try:
            db.execute(
                text(
                    """
                    INSERT INTO kingdom_resource_transfers (
                        from_kingdom_id, to_kingdom_id, resource_type,
                        amount, reason
                    ) VALUES (
                        :from_id, :to_id, :res, :amt, :reason
                    )
                    """
                ),
                {
                    "from_id": from_kingdom_id,
                    "to_id": to_kingdom_id,
                    "res": resource,
                    "amt": amount,
                    "reason": reason or "unlogged",
                },
            )
            db.commit()
        except Exception as exc:
            logger.warning("Failed to log transfer: %s", exc)
