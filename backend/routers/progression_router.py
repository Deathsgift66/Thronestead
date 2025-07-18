# Project Name: Thronestead©
# File Name: progression_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: progression_router.py
Role: API routes for progression router.
Version: 2025-06-21
"""

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.progression_service import calculate_troop_slots, get_total_modifiers

from ..data import get_max_villages_allowed
from ..database import get_db
from ..security import require_user_id

# Allowed characters for noble and knight names (alphanumeric & spaces)
NAME_PATTERN = re.compile(r"^[A-Za-z0-9 ]{1,50}$")

router = APIRouter(prefix="/api/progression", tags=["progression"])


# 🔹 Utility: Get the kingdom ID for a player
def get_kingdom_id(db: Session, user_id: str) -> int:
    """Return the kingdom_id for the given user or raise 404."""
    kid = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    if kid is None:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    return int(kid)


# 🔹 Input Schemas
class NoblePayload(BaseModel):
    noble_name: str

    @validator("noble_name")
    def _validate_name(cls, v: str) -> str:  # noqa: D401
        """Validate noble name format."""
        if not NAME_PATTERN.match(v):
            raise ValueError("Name must be 1-50 alphanumeric characters or spaces")
        return v.strip()


class KnightPayload(BaseModel):
    knight_name: str

    @validator("knight_name")
    def _validate_knight(cls, v: str) -> str:  # noqa: D401
        """Validate knight name format."""
        if not NAME_PATTERN.match(v):
            raise ValueError("Name must be 1-50 alphanumeric characters or spaces")
        return v.strip()


class KnightRenamePayload(BaseModel):
    current_name: str
    new_name: str

    @validator("current_name", "new_name")
    def _validate_rename(cls, v: str) -> str:  # noqa: D401
        """Validate both knight names."""
        if not NAME_PATTERN.match(v):
            raise ValueError("Name must be 1-50 alphanumeric characters or spaces")
        return v.strip()


def _count_records(db: Session, table: str, kid: int) -> int:
    """Return ``COUNT(*)`` for the given table and kingdom."""
    return (
        db.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE kingdom_id = :kid"),
            {"kid": kid},
        ).scalar()
        or 0
    )


def _ensure_records(
    db: Session,
    table: str,
    column: str,
    kid: int,
    required: int,
    prefix: str,
) -> int:
    """Insert placeholder records until ``required`` entries exist."""

    current = _count_records(db, table, kid)

    if current < required:
        rows = [
            {"kid": kid, "name": f"{prefix} {i + 1}"} for i in range(current, required)
        ]
        if rows:
            db.execute(
                text(
                    f"INSERT INTO {table} (kingdom_id, {column})"
                    f" VALUES (:kid, :name)"
                ),
                rows,
            )

    return max(current, required)


def ensure_nobles(db: Session, kid: int, required: int) -> int:
    """Ensure the kingdom has at least ``required`` nobles."""
    return _ensure_records(
        db,
        "kingdom_nobles",
        "noble_name",
        kid,
        required,
        "Noble",
    )


def ensure_knights(db: Session, kid: int, required: int) -> int:
    """Ensure the kingdom has at least ``required`` knights."""
    return _ensure_records(
        db,
        "kingdom_knights",
        "knight_name",
        kid,
        required,
        "Knight",
    )


# 🔹 GET: Castle Level
@router.get("/castle")
def get_castle_level(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    kid = get_kingdom_id(db, user_id)
    level = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchone()

    if not level:
        db.execute(
            text(
                "INSERT INTO kingdom_castle_progression (kingdom_id, castle_level) VALUES (:kid, 1)"
            ),
            {"kid": kid},
        )
        db.execute(
            text(
                "INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT DO NOTHING"
            ),
            {"kid": kid},
        )
        db.commit()
        return {"castle_level": 1}

    return {"castle_level": level[0]}


# 🔹 POST: Upgrade Castle
@router.post("/castle")
def upgrade_castle(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    kid = get_kingdom_id(db, user_id)

    # Upgrade or insert castle level
    db.execute(
        text(
            """
            INSERT INTO kingdom_castle_progression (kingdom_id, castle_level)
            VALUES (:kid, 1)
            ON CONFLICT (kingdom_id) DO UPDATE
                SET castle_level = kingdom_castle_progression.castle_level + 1
            """
        ),
        {"kid": kid},
    )

    # Ensure troop slots record exists
    db.execute(
        text(
            "INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT DO NOTHING"
        ),
        {"kid": kid},
    )
    db.execute(
        text(
            "UPDATE kingdom_troop_slots SET slots_from_buildings = slots_from_buildings + 1 WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    )

    # Get new level after upgrade
    level_row = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchone()
    level = int(level_row[0]) if level_row else 1

    # 💠 Handle Noble Unlocks
    if level >= 2:
        noble_count = ensure_nobles(db, kid, 2)
        db.execute(
            text(
                "UPDATE kingdom_troop_slots SET slots_from_projects = :count WHERE kingdom_id = :kid"
            ),
            {"count": noble_count, "kid": kid},
        )

    # 💠 Handle Knight Unlocks
    if level >= 3:
        required = 1 if level == 3 else 2
        knight_count = ensure_knights(db, kid, required)
        db.execute(
            text(
                "UPDATE kingdom_troop_slots SET slots_from_events = :bonus WHERE kingdom_id = :kid"
            ),
            {"bonus": knight_count * 2, "kid": kid},
        )

    db.commit()
    calculate_troop_slots(db, kid)

    return {"message": "Castle upgraded", "castle_level": level}


# 🔹 POST: Upgrade Castle (explicit route)
@router.post("/castle/upgrade")
def upgrade_castle_explicit(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    """Alias for :func:`upgrade_castle` using a more descriptive path."""
    return upgrade_castle(user_id=user_id, db=db)


# 🔹 GET/POST: Nobles
@router.get("/nobles")
def get_nobles(user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    rows = db.execute(
        text(
            "SELECT noble_name, level, title, loyalty, specialization "
            "FROM kingdom_nobles WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchall()
    nobles = [
        {
            "name": r[0],
            "level": r[1],
            "title": r[2],
            "loyalty": r[3],
            "specialization": r[4],
        }
        for r in rows
    ]
    return {"nobles": nobles}


@router.post("/nobles")
def assign_noble(
    payload: NoblePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)

    db.execute(
        text(
            "INSERT INTO kingdom_nobles (kingdom_id, noble_name) VALUES (:kid, :name)"
        ),
        {"kid": kid, "name": payload.noble_name},
    )

    count = _count_records(db, "kingdom_nobles", kid)

    db.execute(
        text(
            "UPDATE kingdom_troop_slots SET slots_from_projects = :count WHERE kingdom_id = :kid"
        ),
        {"count": count, "kid": kid},
    )

    db.commit()
    calculate_troop_slots(db, kid)
    return {"message": "Noble assigned"}


# 🔹 POST: Rename Noble
class NobleRenamePayload(BaseModel):
    old_name: str
    new_name: str

    @validator("new_name")
    def _validate_new_name(cls, v: str) -> str:  # noqa: D401
        """Validate new noble name format."""
        if not NAME_PATTERN.match(v):
            raise ValueError("Name must be 1-50 alphanumeric characters or spaces")
        return v.strip()


@router.post("/nobles/rename")
def rename_noble(
    payload: NobleRenamePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    result = db.execute(
        text(
            "UPDATE kingdom_nobles SET noble_name = :new WHERE kingdom_id = :kid AND noble_name = :old"
        ),
        {"new": payload.new_name, "kid": kid, "old": payload.old_name},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Noble not found")

    db.commit()
    return {"message": "Noble renamed"}


# 🔹 GET/POST: Knights
@router.get("/knights")
def get_knights(user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    kid = get_kingdom_id(db, user_id)
    rows = db.execute(
        text(
            "SELECT knight_name, rank, level, leadership, tactics, morale_aura "
            "FROM kingdom_knights WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchall()
    knights = [
        {
            "name": r[0],
            "rank": r[1],
            "level": r[2],
            "leadership": r[3],
            "tactics": r[4],
            "morale_aura": r[5],
        }
        for r in rows
    ]
    return {"knights": knights}


@router.post("/knights")
def assign_knight(
    payload: KnightPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)

    db.execute(
        text(
            "INSERT INTO kingdom_knights (kingdom_id, knight_name) VALUES (:kid, :name)"
        ),
        {"kid": kid, "name": payload.knight_name},
    )

    count = _count_records(db, "kingdom_knights", kid)

    db.execute(
        text(
            "UPDATE kingdom_troop_slots SET slots_from_events = :bonus WHERE kingdom_id = :kid"
        ),
        {"bonus": count * 2, "kid": kid},
    )

    db.commit()
    calculate_troop_slots(db, kid)
    return {"message": "Knight assigned"}



# 🔹 POST: Rename Knight
@router.post("/knights/rename")
def rename_knight(
    payload: KnightRenamePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)

    result = db.execute(
        text(
            "UPDATE kingdom_knights SET knight_name = :new WHERE kingdom_id = :kid AND knight_name = :old"
        ),
        {"new": payload.new_name, "kid": kid, "old": payload.current_name},
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Knight not found")

    db.commit()
    return {"message": "Knight renamed"}


# 🗡️ POST: Promote Knight
@router.post("/knights/promote")
def promote_knight(
    payload: KnightPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)

    row = db.execute(
        text(
            "SELECT knight_id, rank FROM kingdom_knights WHERE kingdom_id = :kid AND knight_name = :name"
        ),
        {"kid": kid, "name": payload.knight_name},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Knight not found")

    knight_id, current_rank = row
    ranks = ["Squire", "Knight", "Champion", "Paladin"]
    try:
        idx = ranks.index(current_rank)
        new_rank = ranks[idx + 1] if idx < len(ranks) - 1 else current_rank
    except ValueError:
        new_rank = "Knight"

    db.execute(
        text("UPDATE kingdom_knights SET rank = :rank WHERE knight_id = :id"),
        {"rank": new_rank, "id": knight_id},
    )

    db.commit()
    return {"message": "Knight promoted", "new_rank": new_rank}



# 🔹 POST: Force Recalculate Progression
@router.post("/refresh")
def refresh_progression(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    kid = get_kingdom_id(db, user_id)
    total_slots = calculate_troop_slots(db, kid)
    level = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchone()
    return {"castle_level": level[0] if level else 1, "troop_slots": total_slots}


# 🔹 GET: Summary Overview
@router.get("/summary")
def progression_summary(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    kid = get_kingdom_id(db, user_id)

    level_row = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchone()
    castle_level = level_row[0] if level_row else 1

    nobles = _count_records(db, "kingdom_nobles", kid)

    knights = _count_records(db, "kingdom_knights", kid)

    villages = _count_records(db, "kingdom_villages", kid)

    used_slots = db.execute(
        text("SELECT used_slots FROM kingdom_troop_slots WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    used = used_slots[0] if used_slots else 0
    total = calculate_troop_slots(db, kid)

    return {
        "castle_level": castle_level,
        "max_villages": get_max_villages_allowed(castle_level),
        "current_villages": villages,
        "nobles_total": nobles,
        "nobles_available": nobles,
        "knights_total": knights,
        "knights_available": knights,
        "troop_slots": {
            "used": used,
            "available": max(0, total - used),
        },
    }


# 🔹 GET: Modifiers
@router.get("/modifiers")
def get_modifiers(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    kid = get_kingdom_id(db, user_id)
    return get_total_modifiers(db, kid)
