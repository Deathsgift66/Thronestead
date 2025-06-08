from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session


from ..database import get_db
from services.progression_service import calculate_troop_slots, get_total_modifiers

router = APIRouter(prefix="/api/progression", tags=["progression"])


def get_user_id(x_user_id: str | None = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")
    return x_user_id


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
    user_id: str = Depends(get_user_id),
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
    user_id: str = Depends(get_user_id),
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
            "UPDATE kingdom_troop_slots SET castle_bonus_slots = castle_bonus_slots + 1 WHERE kingdom_id = :kid"
        ),
        {"kid": kid},
    )

    db.commit()

    level = db.execute(
        text("SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]

    calculate_troop_slots(db, kid)

    return {"message": "Castle upgraded", "castle_level": level}


@router.get("/nobles")
def get_nobles(
    user_id: str = Depends(get_user_id),
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
    user_id: str = Depends(get_user_id),
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
            "UPDATE kingdom_troop_slots SET noble_bonus_slots = :count WHERE kingdom_id = :kid"
        ),
        {"count": count, "kid": kid},
    )

    db.commit()

    calculate_troop_slots(db, kid)

    return {"message": "Noble assigned"}


@router.get("/knights")
def get_knights(
    user_id: str = Depends(get_user_id),
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
    user_id: str = Depends(get_user_id),
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
            "UPDATE kingdom_troop_slots SET knight_bonus_slots = :bonus WHERE kingdom_id = :kid"
        ),
        {"bonus": count * 2, "kid": kid},
    )

    db.commit()

    calculate_troop_slots(db, kid)

    return {"message": "Knight assigned"}


@router.post("/refresh")
def refresh_progression(
    user_id: str = Depends(get_user_id),
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
def progression_summary(user_id: str = Depends(get_user_id)):
    state = progression_state.setdefault(user_id, {"castle_level": 1, "nobles": [], "knights": []})
    castle_level = state["castle_level"]
    villages = kingdom_villages.get(1, [])
    mil = military_state.setdefault(1, {
        "base_slots": 20,
        "used_slots": 0,
        "morale": 100,
        "queue": [],
        "history": [],
    })
    used = mil["used_slots"]
    return {
        "castle_level": castle_level,
        "max_villages": get_max_villages_allowed(castle_level),
        "current_villages": len(villages),
        "nobles_total": len(state["nobles"]),
        "nobles_available": len(state["nobles"]),
        "knights_total": len(state["knights"]),
        "knights_available": len(state["knights"]),
        "troop_slots": {
            "used": used,
            "available": max(0, mil["base_slots"] - used),
        },
    }


@router.get("/modifiers")
def get_modifiers(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Return all active modifiers for the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    return get_total_modifiers(db, kid)

