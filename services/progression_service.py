from sqlalchemy import text
from sqlalchemy.orm import Session


def calculate_troop_slots(db: Session, kingdom_id: int) -> int:
    """Calculate the total troop slots for a kingdom and update the database.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session connected to the database.
    kingdom_id : int
        Identifier of the kingdom to update.

    Returns
    -------
    int
        The calculated total troop slot count.
    """
    result = db.execute(
        text(
            """
            SELECT base_slots, castle_bonus_slots, noble_bonus_slots,
                   knight_bonus_slots, building_bonus_slots, tech_bonus_slots,
                   vip_bonus_slots
            FROM troop_slots
            WHERE kingdom_id = :kid
            """
        ),
        {"kid": kingdom_id},
    ).fetchone()

    if not result:
        return 0

    (
        base_slots,
        castle_bonus,
        noble_bonus,
        knight_bonus,
        building_bonus,
        tech_bonus,
        vip_bonus,
    ) = result

    total_slots = (
        base_slots
        + castle_bonus
        + noble_bonus
        + knight_bonus
        + building_bonus
        + tech_bonus
        + vip_bonus
    )

    db.execute(
        text("UPDATE troop_slots SET total_slots = :total WHERE kingdom_id = :kid"),
        {"total": total_slots, "kid": kingdom_id},
    )
    db.commit()

    return total_slots
