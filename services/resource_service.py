# Project Name: Thronestead©
# File Name: resource_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66
"""Service utilities for the kingdom resource economy."""

from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import KingdomResourceTransfer

from .text_utils import sanitize_plain_text

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Core Supported Resource Types (sync with DB ENUM or constants)
# ------------------------------------------------------------------------------

RESOURCE_TYPES = {
    "wood",
    "stone",
    "iron_ore",
    "gold",
    "food",
    "coal",
    "livestock",
    "clay",
    "flax",
    "tools",
    "wood_planks",
    "refined_stone",
    "iron_ingots",
    "charcoal",
    "leather",
    "arrows",
    "swords",
    "axes",
    "shields",
    "armour",
    "wagon",
    "siege_weapons",
    "jewelry",
    "spear",
    "horses",
    "pitchforks",
    "gems",
}

# Fields that should never be returned to clients when using Supabase
# Fields that should never be exposed to clients or modified directly
METADATA_FIELDS = {"kingdom_id", "created_at", "last_updated"}


def fetch_supabase_resources(user_id: str) -> Optional[dict[str, int]]:
    """Fetch a kingdom's resources directly from Supabase."""
    try:
        from backend.supabase_client import get_supabase_client
    except RuntimeError:
        return None

    try:
        supabase = get_supabase_client()
        kid_resp = (
            supabase.table("kingdoms")
            .select("kingdom_id")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if getattr(kid_resp, "status_code", 200) >= 400:
            logger.error(
                "Supabase error fetching kingdom: %s",
                getattr(kid_resp, "error", "unknown"),
            )
            return None

        kid = (getattr(kid_resp, "data", kid_resp) or {}).get("kingdom_id")
        if not kid:
            return None

        res_resp = (
            supabase.table("kingdom_resources")
            .select("*")
            .eq("kingdom_id", kid)
            .single()
            .execute()
        )
        if getattr(res_resp, "status_code", 200) >= 400:
            logger.error(
                "Supabase error fetching resources: %s",
                getattr(res_resp, "error", "unknown"),
            )
            return None

        row = getattr(res_resp, "data", res_resp) or {}
        if not row:
            return None

        return {k: v for k, v in row.items() if k not in METADATA_FIELDS}
    except Exception:
        logger.exception("Error retrieving resources from Supabase")
        return None


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def validate_resource(resource: str) -> None:
    """Raise ``ValueError`` if ``resource`` is not defined in ``RESOURCE_TYPES``."""
    if resource not in RESOURCE_TYPES:
        raise ValueError(f"Invalid resource type: {resource}")


def _apply_resource_changes(
    db: Session,
    kingdom_id: int,
    changes: dict[str, int],
    op: Literal["+", "-"],
    *,
    commit: bool = True,
) -> None:
    """Apply resource increments or decrements atomically.

    Parameters
    ----------
    db : Session
        Active database session.
    kingdom_id : int
        Target kingdom record.
    changes : dict[str, int]
        Mapping of resource name to change amount.
    op : Literal["+", "-"]
        Operation to perform (``"+"`` for gain, ``"-"`` for spend).

    Notes
    -----
    Uses a single ``UPDATE`` statement to modify only the specified
    resource columns, ensuring minimal lock contention even with many
    concurrent updates.
    """

    if not changes:
        return

    set_expr = []
    for res, amt in changes.items():
        validate_resource(res)
        if amt < 0:
            raise ValueError("Resource amounts must be positive")
        set_expr.append(
            f"{res} = COALESCE({res}, 0) + :{res}"
            if op == "+"
            else f"{res} = {res} - :{res}"
        )

    sql = (
        "UPDATE kingdom_resources SET "
        + ", ".join(set_expr)
        + " WHERE kingdom_id = :kid"
    )
    db.execute(text(sql), {**changes, "kid": kingdom_id})
    if commit:
        db.commit()


# ------------------------------------------------------------------------------
# Public Methods
# ------------------------------------------------------------------------------


def initialize_kingdom_resources(
    db: Session, kingdom_id: int, initial: Optional[dict[str, int]] | None = None
) -> None:
    """Create the ``kingdom_resources`` row for ``kingdom_id`` if missing.

    Parameters
    ----------
    db : Session
        Active database session.
    kingdom_id : int
        Target kingdom.
    initial : dict[str, int], optional
        Starting resource amounts to insert. Unspecified columns default to ``0``.
    """

    columns = ["kingdom_id"]
    values = [":kid"]
    params: dict[str, int] = {"kid": kingdom_id}

    for res, amt in (initial or {}).items():
        validate_resource(res)
        if amt < 0:
            raise ValueError("Initial resources must be non-negative")
        columns.append(res)
        values.append(f":{res}")
        params[res] = amt

    sql = (
        f"INSERT INTO kingdom_resources ({', '.join(columns)}) "
        f"VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING"
    )
    db.execute(text(sql), params)
    db.commit()


def ensure_kingdom_resource_row(db: Session, kingdom_id: int) -> None:
    """Create an empty ``kingdom_resources`` row if none exists."""
    exists = db.execute(
        text("SELECT 1 FROM kingdom_resources WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    if not exists:
        db.execute(
            text("INSERT INTO kingdom_resources (kingdom_id) VALUES (:kid)"),
            {"kid": kingdom_id},
        )


def get_kingdom_resources(db: Session, kingdom_id: int, *, lock: bool = False) -> dict:
    """Return current resource values for a kingdom.

    Parameters
    ----------
    db : Session
        Active database session.
    kingdom_id : int
        Target kingdom.
    lock : bool, optional
        If ``True`` acquire a ``FOR UPDATE`` lock on the row so that
        subsequent updates are safe from race conditions.
    """

    sql = "SELECT * FROM kingdom_resources WHERE kingdom_id = :kid"
    if lock:
        sql += " FOR UPDATE"

    row = db.execute(text(sql), {"kid": kingdom_id}).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Kingdom resource row missing.")

    return dict(row)


def spend_resources(
    db: Session, kingdom_id: int, cost: dict[str, int], *, commit: bool = True
) -> None:
    """Deduct specified resources from the kingdom.

    Parameters
    ----------
    db : Session
        Active database session.
    kingdom_id : int
        Target kingdom.
    cost : dict[str, int]
        Resources to spend.

    Notes
    -----
    The resource row is locked using ``FOR UPDATE`` to ensure the
    balance check and deduction occur atomically.
    """
    current = get_kingdom_resources(db, kingdom_id, lock=True)

    for res, amt in cost.items():
        validate_resource(res)
        if amt < 0:
            raise ValueError("Negative spending not allowed")
        if current.get(res, 0) < amt:
            raise HTTPException(status_code=400, detail=f"Not enough {res}")

    _apply_resource_changes(db, kingdom_id, cost, "-", commit=commit)


def gain_resources(
    db: Session, kingdom_id: int, gain: dict[str, int], *, commit: bool = True
) -> None:
    """
    Add specified resources to the kingdom.
    """
    for res, amt in gain.items():
        validate_resource(res)
        if amt < 0:
            raise ValueError("Negative gain not allowed")

    _apply_resource_changes(db, kingdom_id, gain, "+", commit=commit)


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

    clean_reason = sanitize_plain_text(reason, 255)

    try:
        with db.begin():
            # Spend from sender
            spend_resources(
                db,
                from_kingdom_id,
                {resource: amount},
                commit=False,
            )
            # Give to recipient
            gain_resources(db, to_kingdom_id, {resource: amount}, commit=False)

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
                            "reason": clean_reason or "unlogged",
                        },
                    )
                except Exception as exc:
                    logger.warning("Failed to log transfer: %s", exc)
                    raise RuntimeError("transfer log insert failed") from exc
    except Exception:
        db.rollback()
        raise


def adjust_gold(db: Session, kingdom_id: int, amount: int, *, commit: bool = True) -> None:
    """Adjust a kingdom's gold balance up or down."""

    if amount == 0:
        return

    if amount > 0:
        gain_resources(db, kingdom_id, {"gold": amount}, commit=commit)
    else:
        spend_resources(db, kingdom_id, {"gold": -amount}, commit=commit)

