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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services import resource_service

from ..database import get_db
from ..security import require_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/kingdom_troops", tags=["kingdom_troops"])


class UpgradePayload(BaseModel):
    """Input schema for troop upgrades."""

    from_unit: str
    to_unit: str
    quantity: int


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


@router.post("/upgrade")
def upgrade_troops(
    payload: UpgradePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Upgrade troops to a new unit type if requirements are met."""
    kid = get_kingdom_id(db, user_id)

    path = (
        db.execute(
            text(
                "SELECT * FROM unit_upgrade_paths WHERE from_unit_type = :f AND to_unit_type = :t"
            ),
            {"f": payload.from_unit, "t": payload.to_unit},
        )
        .mappings()
        .fetchone()
    )

    if not path:
        raise HTTPException(status_code=404, detail="Upgrade path not found")

    req_level = path.get("required_level", 1)
    cost: dict[str, int] = dict(path.get("cost") or {})
    for res in resource_service.RESOURCE_TYPES:
        amt = path.get(res)
        if amt:
            cost[res] = cost.get(res, 0) + int(amt)

    xp_needed = int(cost.pop("xp", 0))

    row = db.execute(
        text(
            "SELECT quantity, COALESCE(unit_xp, 0) FROM kingdom_troops "
            "WHERE kingdom_id = :kid AND unit_type = :ut AND unit_level = :lvl"
        ),
        {"kid": kid, "ut": payload.from_unit, "lvl": req_level},
    ).fetchone()

    if not row or row[0] < payload.quantity:
        raise HTTPException(status_code=400, detail="Not enough troops")

    if row[1] < xp_needed:
        raise HTTPException(status_code=400, detail="Not enough XP")

    if not resource_service.has_enough_resources(db, kid, cost):
        raise HTTPException(status_code=400, detail="Not enough resources")

    resource_service.spend_resources(db, kid, cost)
    if xp_needed:
        db.execute(
            text(
                "UPDATE kingdom_troops SET unit_xp = unit_xp - :xp "
                "WHERE kingdom_id = :kid AND unit_type = :ut AND unit_level = :lvl"
            ),
            {"xp": xp_needed, "kid": kid, "ut": payload.from_unit, "lvl": req_level},
        )

    db.execute(
        text(
            "UPDATE kingdom_troops SET quantity = quantity - :q "
            "WHERE kingdom_id = :kid AND unit_type = :ut AND unit_level = :lvl"
        ),
        {"q": payload.quantity, "kid": kid, "ut": payload.from_unit, "lvl": req_level},
    )

    db.execute(
        text(
            """
            INSERT INTO kingdom_troops (kingdom_id, unit_type, unit_level, quantity)
            VALUES (:kid, :to, 1, :q)
            ON CONFLICT (kingdom_id, unit_type, unit_level)
            DO UPDATE SET quantity = kingdom_troops.quantity + :q
            """
        ),
        {"kid": kid, "to": payload.to_unit, "q": payload.quantity},
    )

    db.commit()
    return {"status": "upgraded", "unit": payload.to_unit, "quantity": payload.quantity}
