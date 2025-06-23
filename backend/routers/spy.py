# Project Name: Thronestead©
# File Name: spy.py
# Developer: OpenAI's Codex

"""Routes related to spy missions."""

import random
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from ..database import get_db
from ..models import Kingdom
from .progression_router import get_kingdom_id
from ..security import verify_jwt_token
from services import spies_service

router = APIRouter(prefix="/api/spy", tags=["spies"])


class LaunchPayload(BaseModel):
    target_kingdom_name: str = Field(..., description="Name of the target kingdom")
    mission_type: str = Field(..., description="Type of spy mission")
    num_spies: int = Field(..., gt=0, description="Number of spies to send")


DAILY_LIMIT = 5


@router.post("/launch")
def launch_spy_mission(
    payload: LaunchPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Execute a spy mission against another kingdom."""
    kingdom_id = get_kingdom_id(db, user_id)
    attacker_record = spies_service.get_spy_record(db, kingdom_id)
    if payload.num_spies > attacker_record.get("spy_count", 0):
        raise HTTPException(status_code=400, detail="Not enough spies available")

    target = db.execute(
        select(Kingdom).where(Kingdom.kingdom_name == payload.target_kingdom_name)
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target kingdom not found")

    target_record = spies_service.get_spy_record(db, target.kingdom_id)
    if (
        attacker_record.get("daily_attacks_sent", 0) >= DAILY_LIMIT
        or target_record.get("daily_attacks_received", 0) >= DAILY_LIMIT
    ):
        raise HTTPException(status_code=400, detail="Daily spy limit exceeded")

    atk_tech = (
        db.execute(
            select(Kingdom.tech_level).where(Kingdom.kingdom_id == kingdom_id)
        ).scalar_one()
        or 1
    )
    def_tech = target.tech_level or 1
    defense_rating = spies_service.get_spy_defense(db, target.kingdom_id)
    base = 50 + (atk_tech - def_tech) * 5 - defense_rating
    success_pct = max(5.0, min(95.0, float(base)))
    detection_pct = max(5.0, min(95.0, 100.0 - success_pct + defense_rating))
    accuracy_pct = min(100.0, success_pct + 10.0)

    spies_service.start_mission(db, kingdom_id, target.kingdom_id)
    mission_id = spies_service.create_spy_mission(
        db, kingdom_id, payload.mission_type, target.kingdom_id
    )

    success = random.random() * 100 < success_pct
    detected = random.random() * 100 < detection_pct
    spies_lost = 0

    if success:
        spies_service.record_success(db, kingdom_id)
        spies_service.update_mission_status(db, mission_id, "success")
    else:
        spies_lost = random.randint(1, payload.num_spies)
        spies_service.record_losses(db, kingdom_id, spies_lost)
        spies_service.update_mission_status(db, mission_id, "fail")

    if payload.mission_type == "assassination" and success:
        db.execute(
            text(
                "UPDATE village_modifiers SET defense_bonus = defense_bonus - 5 "
                "WHERE village_id IN (SELECT village_id FROM kingdom_villages "
                "WHERE kingdom_id = :kid)"
            ),
            {"kid": target.kingdom_id},
        )
        db.commit()

    return {
        "mission_id": mission_id,
        "outcome": "success" if success else "failed",
        "success_pct": success_pct,
        "detected": detected,
        "accuracy_pct": accuracy_pct,
        "spies_lost": spies_lost,
    }


@router.get("/defense")
async def get_spy_defense(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    """Return the spy defense stats for the player's kingdom."""
    kingdom = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not kingdom:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    defense = db.execute(
        text("SELECT * FROM spy_defense WHERE kingdom_id = :kid"),
        {"kid": kingdom[0]},
    ).fetchone()
    return dict(defense._mapping) if defense else {}


@router.get("/log")
def get_spy_log(
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return recent spy missions for the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT sm.mission_type,
                   sm.target_id,
                   k.kingdom_name AS target_name,
                   sm.status AS outcome,
                   sm.accuracy_percent AS accuracy,
                   sm.was_detected AS detected,
                   sm.spies_killed AS spies_lost,
                   COALESCE(sm.completed_at, sm.launched_at) AS timestamp
              FROM spy_missions sm
         LEFT JOIN kingdoms k ON sm.target_id = k.kingdom_id
             WHERE sm.kingdom_id = :kid
             ORDER BY sm.launched_at DESC
             LIMIT :lim
            """
        ),
        {"kid": kid, "lim": limit},
    ).fetchall()

    logs = [dict(r._mapping) for r in rows]
    return {"logs": logs}
