"""Utility service functions related to progression."""

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
