# Comment
# Project Name: Thronestead©
# File Name: production_tick_service.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
"""Service for applying periodic resource production from villages."""

from __future__ import annotations

import logging
from collections import defaultdict

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore

from . import progression_service
from .resource_service import gain_resources

logger = logging.getLogger(__name__)


def tick_kingdom_production(db: Session, kingdom_id: int) -> dict[str, int]:
    """Apply a single production tick for a kingdom.

    Base production rates from each ``village_production`` row are summed and
    multiplied by the kingdom's aggregated ``production_bonus``. The resulting
    amounts are credited to ``kingdom_resources`` atomically.

    Parameters
    ----------
    db : Session
        Active database session.
    kingdom_id : int
        Target kingdom.

    Returns
    -------
    dict[str, int]
        Mapping of resource type to amount added.
    """

    rows = db.execute(
        text(
            """
            SELECT vp.resource_type,
                   SUM(vp.production_rate * vp.seasonal_multiplier)
              FROM village_production vp
              JOIN kingdom_villages kv ON kv.village_id = vp.village_id
             WHERE kv.kingdom_id = :kid
             GROUP BY vp.resource_type
            """
        ),
        {"kid": kingdom_id},
    ).fetchall()

    base_rates: dict[str, float] = {r[0]: float(r[1] or 0) for r in rows}
    if not base_rates:
        return {}

    mods = progression_service.get_total_modifiers(db, kingdom_id)
    prod_bonus = mods.get("production_bonus", {}) if isinstance(mods, dict) else {}
    total_bonus = sum(float(v) for v in prod_bonus.values()) if isinstance(prod_bonus, dict) else 0.0

    multiplier = 1.0 + (total_bonus / 100.0 if total_bonus else 0.0)
    gained = {res: int(rate * multiplier) for res, rate in base_rates.items()}

    try:
        gain_resources(db, kingdom_id, gained)
    except Exception:
        logger.exception("Failed applying production tick for kingdom %s", kingdom_id)
        raise

    return gained
