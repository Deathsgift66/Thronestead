# Project Name: Kingmakers Rise©
# File Name: progression_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException, Header

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session


from ..database import get_db
from services.progression_service import calculate_troop_slots, get_total_modifiers
from ..data import get_max_villages_allowed
from ..security import require_user_id

router = APIRouter(prefix="/api/progression", tags=["progression"])




def get_kingdom_id(db: Session, user_id: str) -> int:
    """Return the kingdom_id for the given user or raise 404."""
    result = db.execute(
        text("SELECT kingdom_id FROM kingdoms WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    return result[0]


class NoblePayload(BaseModel):
    noble_name: str


class KnightPayload(BaseModel):
    knight_name: str


@router.get("/castle")
def get_castle_level(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    record = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    ).fetchone()
    if not record:
        db.execute(
            text(
                "INSERT INTO kingdom_castle_progression (kingdom_id, castle_level, xp) VALUES (:kid, 1, 0)"
            ),
            {"kid": kid},
        )
        db.execute(
            text(
                "INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT (kingdom_id) DO NOTHING"
            ),
            {"kid": kid},
        )
        db.commit()
        level = 1
    else:
        level = record[0]
    return {"castle_level": level}


@router.post("/castle")
def upgrade_castle(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)

    db.execute(
        text(
            "INSERT INTO kingdom_castle_progression (kingdom_id, castle_level, xp) "
            "VALUES (:kid, 1, 0) "
            "ON CONFLICT (kingdom_id) DO UPDATE SET castle_level = kingdom_castle_progression.castle_level + 1"
        ),
        {"kid": kid},
    )

    # Increase castle bonus slots by one per level
    db.execute(
        text(
            "INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT (kingdom_id) DO NOTHING"
        ),
        {"kid": kid},
    )
    db.execute(
        text(
            "UPDATE kingdom_troop_slots SET slots_from_buildings = slots_from_buildings + 1 WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    )

    db.commit()

    level = db.execute(
        text("SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]

    # automatically grant nobles or knights at key castle levels
    # castle level 2 -> second noble
    if level >= 2:
        noble_count = db.execute(
            text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
            {"kid": kid},
        ).fetchone()[0]
        required = 2
        while noble_count < required:
            db.execute(
                text("INSERT INTO kingdom_nobles (kingdom_id, noble_name) VALUES (:kid, :name)"),
                {"kid": kid, "name": f"Noble {noble_count + 1}"},
            )
            noble_count += 1
        db.execute(
            text("INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT (kingdom_id) DO NOTHING"),
            {"kid": kid},
        )
        db.execute(
            text("UPDATE kingdom_troop_slots SET slots_from_projects = :count WHERE kingdom_id = :kid"),
            {"count": noble_count, "kid": kid},
        )

    # castle level 3 and 4 -> unlock knights
    if level >= 3:
        knight_count = db.execute(
            text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
            {"kid": kid},
        ).fetchone()[0]
        # one knight at level 3, two at level 4+
        required = 1 if level == 3 else 2 if level >= 4 else 0
        while knight_count < required:
            db.execute(
                text("INSERT INTO kingdom_knights (kingdom_id, knight_name) VALUES (:kid, :name)"),
                {"kid": kid, "name": f"Knight {knight_count + 1}"},
            )
            knight_count += 1
        db.execute(
            text("INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT (kingdom_id) DO NOTHING"),
            {"kid": kid},
        )
        db.execute(
            text("UPDATE kingdom_troop_slots SET slots_from_events = :bonus WHERE kingdom_id = :kid"),
            {"bonus": knight_count * 2, "kid": kid},
        )

    db.commit()

    calculate_troop_slots(db, kid)

    return {"message": "Castle upgraded", "castle_level": level}


@router.get("/nobles")
def get_nobles(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    nobles = db.execute(
        text("SELECT noble_name FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchall()
    noble_list = [n[0] for n in nobles]
    return {"nobles": noble_list}


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

    count = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]

    db.execute(
        text(
            "INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT (kingdom_id) DO NOTHING"
        ),
        {"kid": kid},
    )
    db.execute(
        text(
            "UPDATE kingdom_troop_slots SET slots_from_projects = :count WHERE kingdom_id = :kid"
        ),
        {"count": count, "kid": kid},
    )

    db.commit()

    calculate_troop_slots(db, kid)

    return {"message": "Noble assigned"}


@router.get("/knights")
def get_knights(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    knights = db.execute(
        text("SELECT knight_name FROM kingdom_knights WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchall()
    return {"knights": [k[0] for k in knights]}


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

    count = db.execute(
        text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]

    db.execute(
        text(
            "INSERT INTO kingdom_troop_slots (kingdom_id) VALUES (:kid) ON CONFLICT (kingdom_id) DO NOTHING"
        ),
        {"kid": kid},
    )
    db.execute(
        text(
            "UPDATE kingdom_troop_slots SET slots_from_events = :bonus WHERE kingdom_id = :kid"
        ),
        {"bonus": count * 2, "kid": kid},
    )

    db.commit()

    calculate_troop_slots(db, kid)

    return {"message": "Knight assigned"}


@router.post("/refresh")
def refresh_progression(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Recalculate progression related values for the player."""
    kid = get_kingdom_id(db, user_id)
    total_slots = calculate_troop_slots(db, kid)
    level = db.execute(
        text("SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    castle_level = level[0] if level else 1
    return {"castle_level": castle_level, "troop_slots": total_slots}


@router.get("/summary")
def progression_summary(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return a quick overview of castle level, nobles, knights and slots."""
    kid = get_kingdom_id(db, user_id)

    # Castle level ---------------------------------------------------
    row = db.execute(
        text("SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    castle_level = row[0] if row else 1

    # Counts ----------------------------------------------------------
    nobles = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    nobles_count = nobles[0] if nobles else 0

    knights = db.execute(
        text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    knights_count = knights[0] if knights else 0

    villages = db.execute(
        text("SELECT COUNT(*) FROM kingdom_villages WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    village_count = villages[0] if villages else 0

    # Troop slots -----------------------------------------------------
    slots_row = db.execute(
        text("SELECT used_slots FROM kingdom_troop_slots WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()
    used = slots_row[0] if slots_row else 0
    total_slots = calculate_troop_slots(db, kid)

    return {
        "castle_level": castle_level,
        "max_villages": get_max_villages_allowed(castle_level),
        "current_villages": village_count,
        "nobles_total": nobles_count,
        "nobles_available": nobles_count,
        "knights_total": knights_count,
        "knights_available": knights_count,
        "troop_slots": {
            "used": used,
            "available": max(0, total_slots - used),
        },
    }


@router.get("/modifiers")
def get_modifiers(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return all active modifiers for the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    return get_total_modifiers(db, kid)

