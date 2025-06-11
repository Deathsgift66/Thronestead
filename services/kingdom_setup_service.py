from typing import Optional

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore

START_RESOURCES = {
    "wood": 500,
    "stone": 500,
    "food": 300,
    "gold": 200,
}

START_BUILDINGS = [
    "Town Center",
    "Granary",
    "Barracks",
    "Farm",
    "Warehouse",
]

# Default noble created for every new kingdom
DEFAULT_NOBLE_NAME = "Founding Noble"


def create_kingdom_transaction(
    db: Session,
    user_id: str,
    kingdom_name: str,
    region: str,
    village_name: str,
    ruler_title: Optional[str] = None,
    banner_image: Optional[str] = None,
    emblem_image: Optional[str] = None,
    motto: Optional[str] = None,
) -> int:
    """Create a new kingdom and related records. Returns the kingdom_id."""
    try:
        row = db.execute(
            text(
                """
                INSERT INTO kingdoms (user_id, kingdom_name, region)
                VALUES (:uid, :name, :region)
                RETURNING kingdom_id
                """
            ),
            {"uid": user_id, "name": kingdom_name, "region": region},
        ).fetchone()
        if not row:
            raise ValueError("failed")
        kingdom_id = int(row[0])

        vil_row = db.execute(
            text(
                """
                INSERT INTO kingdom_villages (kingdom_id, village_name, is_capital)
                VALUES (:kid, :vname, TRUE)
                RETURNING village_id
                """
            ),
            {"kid": kingdom_id, "vname": village_name},
        ).fetchone()
        village_id = int(vil_row[0]) if vil_row else None

        db.execute(
            text(
                """
                INSERT INTO kingdom_resources (kingdom_id, wood, stone, food, gold)
                VALUES (:kid, :wood, :stone, :food, :gold)
                """
            ),
            {"kid": kingdom_id, **START_RESOURCES},
        )

        db.execute(
            text(
                "INSERT INTO kingdom_troop_slots (kingdom_id, base_slots) VALUES (:kid, 20)"
            ),
            {"kid": kingdom_id},
        )

        # Insert the first noble so progression can begin immediately
        db.execute(
            text(
                "INSERT INTO kingdom_nobles (kingdom_id, noble_name) VALUES (:kid, :name)"
            ),
            {"kid": kingdom_id, "name": DEFAULT_NOBLE_NAME},
        )

        db.execute(
            text(
                """
                UPDATE users
                   SET setup_complete = TRUE,
                       kingdom_name = :name,
                       region = :region,
                       kingdom_id = :kid
                 WHERE user_id = :uid
                """
            ),
            {"name": kingdom_name, "region": region, "kid": kingdom_id, "uid": user_id},
        )

        db.commit()
        return kingdom_id
    except Exception:
        db.rollback()
        raise
