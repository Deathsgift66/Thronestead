# Comment
# Project Name: Thronestead©
# File Name: village_modifiers.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: village_modifiers.py
Role: API routes for village modifiers.
Version: 2025-06-21
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from backend.models import VillageModifier

from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/village_modifiers", tags=["village_modifiers"])


# === Payload schema for applying village modifiers ===
class ModifierPayload(BaseModel):
    village_id: int
    resource_bonus: dict | None = None
    troop_bonus: dict | None = None
    construction_speed_bonus: float | None = None
    defense_bonus: float | None = None
    trade_bonus: float | None = None
    source: str
    stacking_rules: dict | None = None
    expires_at: datetime | None = None
    applied_by: str | None = None


# === GET: List all active modifiers for a village ===
@router.get("/{village_id}", summary="List Active Modifiers")
def list_modifiers(
    village_id: int,
    _uid: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Return all active modifiers for the given village.
    Expired modifiers are automatically excluded.
    """
    rows = (
        db.query(VillageModifier)
        .filter(VillageModifier.village_id == village_id)
        .filter(
            (VillageModifier.expires_at.is_(None))
            | (VillageModifier.expires_at > func.now())
        )
        .all()
    )
    return {
        "modifiers": [
            {
                "village_id": r.village_id,
                "resource_bonus": r.resource_bonus,
                "troop_bonus": r.troop_bonus,
                "construction_speed_bonus": r.construction_speed_bonus,
                "defense_bonus": r.defense_bonus,
                "trade_bonus": r.trade_bonus,
                "source": r.source,
                "stacking_rules": r.stacking_rules,
                "expires_at": r.expires_at,
                "applied_by": r.applied_by,
                "created_at": r.created_at,
                "last_updated": r.last_updated,
            }
            for r in rows
        ]
    }


# === POST: Apply or update a modifier ===
@router.post("/apply", summary="Apply Village Modifier")
def apply_modifier(
    payload: ModifierPayload,
    _uid: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Apply or update a modifier via an upsert."""

    db.execute(
        text(
            """
            INSERT INTO village_modifiers (
                village_id, resource_bonus, troop_bonus,
                construction_speed_bonus, defense_bonus,
                trade_bonus, source, stacking_rules, expires_at,
                applied_by
            ) VALUES (
                :village_id, :resource_bonus, :troop_bonus,
                :csb, :def_bonus, :trade_bonus, :source,
                :stacking_rules, :expires_at, :applied_by
            )
            ON CONFLICT (village_id, source) DO UPDATE
            SET resource_bonus = EXCLUDED.resource_bonus,
                troop_bonus = EXCLUDED.troop_bonus,
                construction_speed_bonus = EXCLUDED.construction_speed_bonus,
                defense_bonus = EXCLUDED.defense_bonus,
                trade_bonus = EXCLUDED.trade_bonus,
                stacking_rules = EXCLUDED.stacking_rules,
                expires_at = EXCLUDED.expires_at,
                applied_by = EXCLUDED.applied_by,
                last_updated = NOW()
            """
        ),
        {
            "village_id": payload.village_id,
            "resource_bonus": payload.resource_bonus or {},
            "troop_bonus": payload.troop_bonus or {},
            "csb": payload.construction_speed_bonus or 0,
            "def_bonus": payload.defense_bonus or 0,
            "trade_bonus": payload.trade_bonus or 0,
            "source": payload.source,
            "stacking_rules": payload.stacking_rules or {},
            "expires_at": payload.expires_at,
            "applied_by": payload.applied_by,
        },
    )

    db.commit()
    return {"message": "modifier applied"}


# === POST: Cleanup expired modifiers ===
@router.post("/cleanup_expired", summary="Purge Expired Modifiers")
def cleanup_expired(
    _uid: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Remove all expired modifiers from the database.
    This keeps the system lean and fast.
    """
    deleted = (
        db.query(VillageModifier)
        .filter(
            VillageModifier.expires_at.is_not(None),
            VillageModifier.expires_at < func.now(),
        )
        .delete()
    )
    db.commit()
    return {"deleted": deleted}
