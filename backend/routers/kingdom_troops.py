# Project Name: Thronestead©
# File Name: kingdom_troops.py
# Version 6.14.2025
# Developer: Codex
"""
Project: Thronestead ©
File: kingdom_troops.py
Role: API routes for kingdom troops.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/kingdom_troops", tags=["kingdom_troops"])


@router.get("/unlocked")
def unlocked_troops(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return the list of unlocked troop types and their stats."""
    kid = get_kingdom_id(db, user_id)

    row = db.execute(
        text("SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    castle_level = row[0] if row else 1

    tech_rows = db.execute(
        text(
            "SELECT tech_code FROM kingdom_research_tracking "
            "WHERE kingdom_id = :kid AND status = 'completed'"
        ),
        {"kid": kid},
    ).fetchall()
    completed = {r[0] for r in tech_rows}

    rows = db.execute(
        text(
            """
            SELECT tc.unit_name AS name,
                   tc.prerequisite_tech,
                   tc.prerequisite_castle_level,
                   us.unit_type,
                   us.tier,
                   us.class,
                   us.damage,
                   us.defense,
                   us.hp,
                   us.speed,
                   us.range
              FROM training_catalog tc
              JOIN unit_stats us ON us.unit_type = tc.unit_name
            ORDER BY us.tier
            """
        )
    ).fetchall()

    unlocked: list[str] = []
    stats: dict[str, dict] = {}
    for (
        name,
        prereq,
        req_level,
        unit_type,
        tier,
        cls,
        dmg,
        defense,
        hp,
        speed,
        rng,
    ) in rows:
        if req_level and castle_level < req_level:
            continue
        if prereq and prereq not in completed:
            continue
        unlocked.append(unit_type)
        stats[unit_type] = {
            "unit_type": unit_type,
            "name": name,
            "tier": tier,
            "class": cls,
            "damage": dmg,
            "defense": defense,
            "hp": hp,
            "speed": speed,
            "range": rng,
        }

    return {"unlockedUnits": unlocked, "unitStats": stats}
