# Project Name: Kingmakers Rise©
# File Name: kingdom_setup_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from typing import Optional
import json
import logging

from services import notification_service

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore

START_RESOURCES = {
    "wood": 100,
    "stone": 100,
    "food": 1000,
    "gold": 200,
}

START_BUILDINGS = []

# Base tech granted if catalogue is empty
STARTER_TECH_CODE = "basic_mining"

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
        ruler_row = db.execute(
            text("SELECT display_name FROM users WHERE user_id = :uid"),
            {"uid": user_id},
        ).fetchone()
        ruler_name = ruler_row[0] if ruler_row else None

        custom = {}
        if banner_image:
            custom["banner_url"] = banner_image
        if emblem_image:
            custom["emblem_url"] = emblem_image
        if ruler_title:
            custom["ruler_title"] = ruler_title

        row = db.execute(
            text(
                """
                INSERT INTO kingdoms (user_id, kingdom_name, region, ruler_name, motto, customizations)
                VALUES (:uid, :name, :region, :rname, :motto, :cust)
                RETURNING kingdom_id
                """
            ),
            {
                "uid": user_id,
                "name": kingdom_name,
                "region": region,
                "rname": ruler_name,
                "motto": motto,
                "cust": json.dumps(custom),
            },
        ).fetchone()
        if not row:
            raise ValueError("failed")
        kingdom_id = int(row[0])

        vil_row = db.execute(
            text(
                """
                INSERT INTO kingdom_villages (kingdom_id, village_name, village_type)
                VALUES (:kid, :vname, 'capital')
                RETURNING village_id
                """
            ),
            {"kid": kingdom_id, "vname": village_name},
        ).fetchone()
        village_id = int(vil_row[0]) if vil_row else None

        # Starter castle
        db.execute(
            text(
                """
                INSERT INTO village_buildings (village_id, building_id, level)
                VALUES (:village_id, 1, 1)
                ON CONFLICT DO NOTHING
                """
            ),
            {"village_id": village_id},
        )

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


        # Fallback building: ensure the starting village has a castle
        db.execute(
            text(
                "INSERT INTO village_buildings (village_id, building_id, level) "
                "VALUES (:vid, 1, 1) ON CONFLICT DO NOTHING"
            ),
            {"vid": village_id},

        )

        # Insert the first noble so progression can begin immediately
        db.execute(
            text(
                "INSERT INTO kingdom_nobles (kingdom_id, noble_name) VALUES (:kid, :name)"
            ),
            {"kid": kingdom_id, "name": DEFAULT_NOBLE_NAME},
        )

        # Optional default tables to avoid null lookups
        db.execute(
            text("INSERT INTO kingdom_spies (kingdom_id) VALUES (:kid)"),
            {"kid": kingdom_id},
        )
        db.execute(
            text(
                "INSERT INTO kingdom_religion (kingdom_id, religion_name, faith_level) "
                "VALUES (:kid, 'None', 1) ON CONFLICT DO NOTHING"
            ),
            {"kid": kingdom_id},
        )

        tech_row = db.execute(
            text("SELECT tech_code FROM tech_catalogue LIMIT 1")
        ).fetchone()
        if tech_row:
            db.execute(
                text(
                    "INSERT INTO kingdom_research_tracking (kingdom_id, tech_code, status) "
                    "VALUES (:kid, :code, 'locked') ON CONFLICT DO NOTHING"
                ),
                {"kid": kingdom_id, "code": tech_row[0]},
            )
        else:
            db.execute(
                text(
                    "INSERT INTO kingdom_research_tracking (kingdom_id, tech_code, status) "
                    "VALUES (:kid, :tech, 'locked') ON CONFLICT DO NOTHING"
                ),
                {"kid": kingdom_id, "tech": STARTER_TECH_CODE},
            )

        # Fallback research tracking if none were inserted
        db.execute(
            text(
                "INSERT INTO kingdom_research_tracking (kingdom_id, tech_code, status) "
                "VALUES (:kid, 'basic_mining', 'locked') ON CONFLICT DO NOTHING"
            ),
            {"kid": kingdom_id},
        )

        db.execute(
            text(
                "INSERT INTO audit_log (user_id, action, details) "
                "VALUES (:uid, 'kingdom_create', :det)"
            ),
            {"uid": user_id, "det": f'Created kingdom {kingdom_name}'},
        )

        db.execute(
            text(
                "INSERT INTO kingdom_history_log (kingdom_id, event_type, event_details) "
                "VALUES (:kid, 'created', :det)"
            ),
            {"kid": kingdom_id, "det": f'Kingdom {kingdom_name} created'},
        )

        db.execute(
            text(
                "INSERT INTO kingdom_vip_status (user_id, vip_level) "
                "VALUES (:uid, 0) ON CONFLICT (user_id) DO NOTHING"
            ),
            {"uid": user_id},
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

        db.execute(
            text(
                """
                INSERT INTO user_setting_entries (user_id, setting_key, setting_value)
                VALUES (:uid, 'theme', 'default')
                ON CONFLICT DO NOTHING
                """
            ),
            {"uid": user_id},
        )

        db.commit()

        notification_service.notify_user(
            db,
            user_id,
            f"Your kingdom '{kingdom_name}' has been established."
        )
        return kingdom_id
    except Exception:
        db.rollback()
        raise
