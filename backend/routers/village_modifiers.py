# Project Name: Thronestead©
# File Name: village_modifiers.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ..database import get_db
from ..security import require_user_id
from backend.models import VillageModifier

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
@router.get("/{village_id}", summary="List Active Modifiers", response_model=None)
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
@router.post("/apply", summary="Apply Village Modifier", response_model=None)
def apply_modifier(
    payload: ModifierPayload,
    _uid: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Apply or update a modifier for a specific village based on the source tag.
    This supports stacking rules and time-based expiration.
    """
    existing = db.query(VillageModifier).filter(
        VillageModifier.village_id == payload.village_id
    ).first()

    if existing:
        # Update existing modifier
        existing.resource_bonus = payload.resource_bonus or {}
        existing.troop_bonus = payload.troop_bonus or {}
        existing.construction_speed_bonus = payload.construction_speed_bonus or 0
        existing.defense_bonus = payload.defense_bonus or 0
        existing.trade_bonus = payload.trade_bonus or 0
        existing.stacking_rules = payload.stacking_rules or {}
        existing.expires_at = payload.expires_at
        existing.applied_by = payload.applied_by
        existing.last_updated = func.now()
    else:
        # Insert new modifier
        mod = VillageModifier(
            village_id=payload.village_id,
            resource_bonus=payload.resource_bonus or {},
            troop_bonus=payload.troop_bonus or {},
            construction_speed_bonus=payload.construction_speed_bonus or 0,
            defense_bonus=payload.defense_bonus or 0,
            trade_bonus=payload.trade_bonus or 0,
            source=payload.source,
            stacking_rules=payload.stacking_rules or {},
            expires_at=payload.expires_at,
            applied_by=payload.applied_by,
        )
        db.add(mod)

    db.commit()
    return {"message": "modifier applied"}


# === POST: Cleanup expired modifiers ===
@router.post("/cleanup_expired", summary="Purge Expired Modifiers", response_model=None)
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
