"""Utility service functions related to progression."""

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


def calculate_troop_slots(db: Session, kingdom_id: int) -> int:
    """Calculate and return the total troop slots for a kingdom.

    The database stores individual bonus columns. This helper aggregates them
    and returns the total. No table currently persists the total, so callers
    may persist the value if desired.
    """

    result = db.execute(
        text(
            """
            SELECT base_slots, castle_bonus_slots, noble_bonus_slots,
                   knight_bonus_slots
            FROM kingdom_troop_slots
            WHERE kingdom_id = :kid
            """
        ),
        {"kid": kingdom_id},
    ).fetchone()

    if not result:
        return 0

    base_slots, castle_bonus, noble_bonus, knight_bonus = result

    total_slots = base_slots + castle_bonus + noble_bonus + knight_bonus

    return total_slots


def check_progression_requirements(
    db: Session,
    kingdom_id: int,
    required_castle_level: int = 0,
    required_nobles: int = 0,
    required_knights: int = 0,
) -> None:
    """Validate castle level, noble and knight requirements.

    Raises ``HTTPException`` with status code 403 if any requirement is unmet.
    """

    # Castle level defaults to 1 if no record exists yet
    castle_record = db.execute(
        text(
            "SELECT castle_level FROM kingdom_castle_progression WHERE kingdom_id = :kid"
        ),
        {"kid": kingdom_id},
    ).fetchone()
    castle_level = castle_record[0] if castle_record else 1

    if castle_level < required_castle_level:
        raise HTTPException(status_code=403, detail="Castle level too low")

    nobles = db.execute(
        text("SELECT COUNT(*) FROM kingdom_nobles WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()[0]
    if nobles < required_nobles:
        raise HTTPException(status_code=403, detail="Not enough nobles")

    knights = db.execute(
        text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()[0]
    if knights < required_knights:
        raise HTTPException(status_code=403, detail="Not enough knights")


def check_troop_slots(db: Session, kingdom_id: int, troops_requested: int) -> None:
    """Ensure the kingdom has enough free troop slots for a request."""

    record = db.execute(
        text(
            """
            SELECT base_slots, castle_bonus_slots, noble_bonus_slots,
                   knight_bonus_slots, used_slots
            FROM kingdom_troop_slots
            WHERE kingdom_id = :kid
            """
        ),
        {"kid": kingdom_id},
    ).fetchone()

    if not record:
        total_slots = 0
        used_slots = 0
    else:
        base, castle_bonus, noble_bonus, knight_bonus, used_slots = record
        total_slots = base + castle_bonus + noble_bonus + knight_bonus

    if used_slots + troops_requested > total_slots:
        raise HTTPException(status_code=400, detail="Not enough troop slots")
