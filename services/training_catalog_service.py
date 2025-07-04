# Project Name: Thronestead©
# File Name: training_catalog_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
# Description: Helpers for reading the training_catalog table.

from __future__ import annotations

import logging
from typing import Optional

from services.sqlalchemy_support import Session, SQLAlchemyError, text

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Unit Catalog Querying
# ------------------------------------------------------------


def list_units(db: Session) -> list[dict]:
    """
    Fetches all available unit types from the training_catalog.

    Returns:
        List[dict]: List of unit definitions ordered by tier.
    """
    try:
        rows = db.execute(
            text("SELECT * FROM training_catalog ORDER BY tier ASC")
        ).fetchall()
        return [dict(row._mapping) for row in rows]

    except SQLAlchemyError:
        logger.exception("Failed to fetch training catalog.")
        return []


def get_unit_by_code(db: Session, unit_id: int) -> Optional[dict]:
    """
    Fetch a single unit definition by unit_id.

    Args:
        unit_id: The numerical ID of the unit to retrieve

    Returns:
        dict | None: Unit definition if found
    """
    try:
        row = db.execute(
            text("SELECT * FROM training_catalog WHERE unit_id = :uid"),
            {"uid": unit_id},
        ).fetchone()
        return dict(row._mapping) if row else None

    except SQLAlchemyError:
        logger.warning("Failed to get unit_id %s", unit_id)
        return None


def list_units_by_tier(db: Session, tier: int) -> list[dict]:
    """
    Return all units for a specific tier.

    Args:
        tier: Unit tier (e.g., 1 for Militia, 3 for Royal Guard)

    Returns:
        List[dict]: All matching unit records
    """
    try:
        rows = db.execute(
            text("SELECT * FROM training_catalog WHERE tier = :tier ORDER BY unit_id"),
            {"tier": tier},
        ).fetchall()
        return [dict(row._mapping) for row in rows]

    except SQLAlchemyError:
        logger.warning("Failed to list units for tier %d", tier)
        return []
