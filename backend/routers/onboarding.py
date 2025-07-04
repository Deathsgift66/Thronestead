# Project Name: Thronestead©
# File Name: onboarding.py
# Version: 7/1/2025
# Developer: Deathsgift66
"""Onboarding helpers to create kingdom records step by step."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.resource_service import initialize_kingdom_resources
from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class KingdomPayload(BaseModel):
    kingdom_name: str
    region: str


class VillagePayload(BaseModel):
    village_name: str


class NoblePayload(BaseModel):
    noble_name: str

    @validator("noble_name")
    def _name(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError("Invalid name")
        return v.strip()


class KnightPayload(BaseModel):
    knight_name: str

    @validator("knight_name")
    def _name(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError("Invalid name")
        return v.strip()


@router.get("/status")
def status(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return which onboarding steps have been completed."""
    row = db.execute(
        text("SELECT kingdom_id, setup_complete FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    kingdom_id = row[0] if row else None
    progress = {
        "user": bool(row),
        "kingdom": False,
        "village": False,
        "resources": False,
        "troop_slots": False,
        "noble": False,
        "knight": False,
        "title": False,
        "complete": bool(row[1]) if row else False,
    }
    if kingdom_id:
        progress["kingdom"] = True
        kid = int(kingdom_id)
        progress["village"] = bool(
            db.execute(
                text("SELECT 1 FROM kingdom_villages WHERE kingdom_id = :kid"),
                {"kid": kid},
            ).fetchone()
        )
        progress["resources"] = bool(
            db.execute(
                text("SELECT 1 FROM kingdom_resources WHERE kingdom_id = :kid"),
                {"kid": kid},
            ).fetchone()
        )
        progress["troop_slots"] = bool(
            db.execute(
                text("SELECT 1 FROM kingdom_troop_slots WHERE kingdom_id = :kid"),
                {"kid": kid},
            ).fetchone()
        )
        progress["noble"] = bool(
            db.execute(
                text("SELECT 1 FROM kingdom_nobles WHERE kingdom_id = :kid"),
                {"kid": kid},
            ).fetchone()
        )
        progress["knight"] = bool(
            db.execute(
                text("SELECT 1 FROM kingdom_knights WHERE kingdom_id = :kid"),
                {"kid": kid},
            ).fetchone()
        )
        progress["title"] = bool(
            db.execute(
                text("SELECT 1 FROM kingdom_titles WHERE kingdom_id = :kid"),
                {"kid": kid},
            ).fetchone()
        )
    return progress


@router.post("/kingdom")
def create_kingdom(
    payload: KingdomPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            "INSERT INTO kingdoms (user_id, kingdom_name, region) "
            "VALUES (:uid, :name, :region) "
            "ON CONFLICT (user_id) DO UPDATE SET kingdom_name = EXCLUDED.kingdom_name, region = EXCLUDED.region "
            "RETURNING kingdom_id"
        ),
        {"uid": user_id, "name": payload.kingdom_name, "region": payload.region},
    ).fetchone()
    kingdom_id = int(row[0]) if row else None
    db.commit()
    if not kingdom_id:
        raise HTTPException(status_code=400, detail="kingdom failed")
    return {"kingdom_id": kingdom_id}


@router.post("/village")
def create_village(
    payload: VillagePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    if kid is None:
        raise HTTPException(status_code=404, detail="kingdom missing")
    db.execute(
        text(
            "INSERT INTO kingdom_villages (kingdom_id, village_name, village_type) "
            "VALUES (:kid, :name, 'capital') ON CONFLICT DO NOTHING"
        ),
        {"kid": kid, "name": payload.village_name},
    )
    db.commit()
    return {"village": "created"}


@router.post("/resources")
def create_resources(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    row = db.execute(
        text("SELECT kingdom_id, region FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="kingdom missing")
    kid, region = int(row[0]), row[1]
    bonus_row = db.execute(
        text("SELECT resource_bonus FROM region_catalogue WHERE region_code = :c"),
        {"c": region},
    ).fetchone()
    bonus = bonus_row[0] if bonus_row else {}
    base = {"wood": 100, "stone": 100, "food": 1000, "gold": 200}
    if isinstance(bonus, dict):
        for res, pct in bonus.items():
            if res in base:
                try:
                    base[res] = int(base[res] * (1 + float(pct) / 100))
                except (ValueError, TypeError):
                    pass
    initialize_kingdom_resources(db, kid, base)
    return {"resources": "created"}


@router.post("/troop_slots")
def create_troop_slots(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    kid = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    if kid is None:
        raise HTTPException(status_code=404, detail="kingdom missing")
    db.execute(
        text(
            "INSERT INTO kingdom_troop_slots (kingdom_id, base_slots) VALUES (:kid, 20) "
            "ON CONFLICT DO NOTHING"
        ),
        {"kid": kid},
    )
    db.commit()
    return {"troop_slots": "created"}


@router.post("/noble")
def create_noble(
    payload: NoblePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    if kid is None:
        raise HTTPException(status_code=404, detail="kingdom missing")
    db.execute(
        text(
            "INSERT INTO kingdom_nobles (kingdom_id, noble_name) VALUES (:kid, :name) "
            "ON CONFLICT DO NOTHING"
        ),
        {"kid": kid, "name": payload.noble_name},
    )
    db.commit()
    return {"noble": "created"}


@router.post("/knight")
def create_knight(
    payload: KnightPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    if kid is None:
        raise HTTPException(status_code=404, detail="kingdom missing")
    db.execute(
        text(
            "INSERT INTO kingdom_knights (kingdom_id, knight_name) VALUES (:kid, :name) "
            "ON CONFLICT DO NOTHING"
        ),
        {"kid": kid, "name": payload.knight_name},
    )
    db.commit()
    return {"knight": "created"}


@router.post("/title")
def grant_title(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    kid = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    if kid is None:
        raise HTTPException(status_code=404, detail="kingdom missing")
    existing = db.execute(
        text(
            "SELECT 1 FROM kingdom_titles WHERE kingdom_id = :kid AND title = 'Thronebound Founder'"
        ),
        {"kid": kid},
    ).fetchone()
    if not existing:
        db.execute(
            text(
                "INSERT INTO kingdom_titles (kingdom_id, title) VALUES (:kid, 'Thronebound Founder')"
            ),
            {"kid": kid},
        )
        db.commit()
    return {"title": "granted"}


@router.post("/complete")
def mark_complete(
    user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)
):
    db.execute(
        text("UPDATE users SET setup_complete = TRUE WHERE user_id = :uid"),
        {"uid": user_id},
    )
    db.commit()
    return {"status": "complete"}
