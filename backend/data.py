# Project Name: Kingmakers Rise©
# File Name: data.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
# Simple in-memory data store for the demo API

# Recruitable units for all kingdoms
recruitable_units = [
    {
        "id": 1,
        "name": "Swordsman",
        "type": "Infantry",
        "training_time": 60,
        "cost": {"gold": 10, "food": 5},
    },
    {
        "id": 2,
        "name": "Archer",
        "type": "Ranged",
        "training_time": 45,
        "cost": {"gold": 8, "wood": 5},
    },
]

# Kingdom military state keyed by kingdom_id
military_state = {
    1: {
        "base_slots": 20,
        "used_slots": 0,
        "morale": 100,
        "queue": [],
        "history": [],
    }
}

# Simplified castle progression tracking
castle_progression_state = {
    1: {
        "castle_level": 1,
        "nobles": 0,
        "knights": 0,
    }
}

# Default regions used when the database table is missing or empty
DEFAULT_REGIONS = [
    {
        "region_code": "north",
        "region_name": "Northlands",
        "description": "Cold and rugged with hardy people.",
        "resource_bonus": {"wood": 50},
        "troop_bonus": {"infantry_hp": 2},
    },
    {
        "region_code": "south",
        "region_name": "Southlands",
        "description": "Fertile fields and warm climate.",
        "resource_bonus": {"food": 100},
        "troop_bonus": {"cavalry_speed": 1},
    },
    {
        "region_code": "east",
        "region_name": "Eastreach",
        "description": "Rich trade routes and culture.",
        "resource_bonus": {"gold": 20},
        "troop_bonus": {"archer_damage": 3},
    },
    {
        "region_code": "west",
        "region_name": "Westvale",
        "description": "Frontier lands full of stone.",
        "resource_bonus": {"stone": 50},
        "troop_bonus": {},
    },
]

# Active kingdom projects keyed by kingdom_id
kingdom_projects: dict[int, list[dict]] = {}

# List of villages currently controlled by each kingdom
kingdom_villages: dict[int, list[dict]] = {}

# Basic mapping for how many villages a castle level supports
def get_max_villages_allowed(castle_level: int) -> int:
    """Return the number of villages allowed for the given castle level."""
    return castle_level

# VIP levels per user_id
vip_levels: dict[str, int] = {}

# Titles and prestige tracking per user
player_titles: dict[str, list[str]] = {}
prestige_scores: dict[str, int] = {}

# Treaty records
kingdom_treaties: dict[int, list[dict]] = {}
alliance_treaties: dict[int, list[dict]] = {}

# Spy related data
kingdom_spies: dict[int, dict] = {}
spy_missions: dict[int, list[dict]] = {}

# Global settings loaded from the database
global_game_settings: dict[str, object] = {}

import logging

try:  # pragma: no cover - SQLAlchemy optional in tests
    from sqlalchemy import text
    from .database import SessionLocal
except ImportError:  # pragma: no cover - fallback when deps missing
    text = lambda q: q  # type: ignore
    SessionLocal = None  # type: ignore


def load_game_settings() -> None:
    """Load active game settings from the database into memory."""
    if not SessionLocal:
        return
    session = SessionLocal()
    try:
        rows = session.execute(
            text(
                "SELECT setting_key, setting_value FROM game_settings WHERE is_active = true"
            )
        ).fetchall()
        global_game_settings.clear()
        for key, value in rows:
            global_game_settings[key] = value
    except Exception as exc:
        logging.error("Failed to load game settings: %s", exc)
    finally:
        session.close()
