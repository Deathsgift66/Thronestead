# Comment
# Project Name: Thronestead©
# File Name: data.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""
This module serves as a runtime in-memory state layer and lightweight cache
for demo, simulation, and real-time performance buffers in Thronestead©.
"""

import logging
from typing import Any, Dict, List

# Set up logger for internal debugging
logger = logging.getLogger("Thronestead.Data")

# ---------------------------------------------------
# ⚔️ Recruitable Units (Stub/demo units for simulation)
# ---------------------------------------------------
recruitable_units: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Swordsman",
        "type": "Infantry",
        "training_time": 60,  # in seconds
        "cost": {"gold": 10, "food": 5},
        "is_support": False,
        "is_siege": False,
    },
    {
        "id": 2,
        "name": "Archer",
        "type": "Ranged",
        "training_time": 45,
        "cost": {"gold": 8, "wood": 5},
        "is_support": False,
        "is_siege": False,
    },
    {
        "id": 3,
        "name": "Catapult",
        "type": "Siege",
        "training_time": 120,
        "cost": {"gold": 20, "wood": 10},
        "is_support": False,
        "is_siege": True,
    },
    {
        "id": 4,
        "name": "Cleric",
        "type": "Support",
        "training_time": 90,
        "cost": {"gold": 15, "food": 8},
        "is_support": True,
        "is_siege": False,
    },
]

# ---------------------------------------------------
# 🛡️ Kingdom Military State
# ---------------------------------------------------
military_state: Dict[int, Dict[str, Any]] = {
    1: {
        "base_slots": 20,
        "used_slots": 0,
        "morale": 100,
        "queue": [],  # active training queue
        "history": [],  # completed training logs
    }
}

# ---------------------------------------------------
# 🏰 Castle Progression
# ---------------------------------------------------
castle_progression_state: Dict[int, Dict[str, int]] = {
    1: {
        "castle_level": 1,
        "nobles": 0,
        "knights": 0,
    }
}

# ---------------------------------------------------
# 🌍 Default Region Metadata (used when DB fails/missing)
# ---------------------------------------------------
DEFAULT_REGIONS: List[Dict[str, Any]] = [
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

# ---------------------------------------------------
# 🏗️ Runtime Buffers and State Caches
# ---------------------------------------------------
kingdom_projects: Dict[int, List[Dict]] = {}
kingdom_villages: Dict[int, List[Dict]] = {}


# Function to determine village cap based on castle level
def get_max_villages_allowed(castle_level: int) -> int:
    """Return the number of villages a kingdom can support based on castle level."""
    return castle_level


# 👑 VIP, Prestige, and Titles
vip_levels: Dict[str, int] = {}  # user_id → vip_level
player_titles: Dict[str, List[str]] = {}  # user_id → list of title strings
prestige_scores: Dict[str, int] = {}  # user_id → prestige points

# 🤝 Diplomacy
kingdom_treaties: Dict[int, List[Dict]] = {}
alliance_treaties: Dict[int, List[Dict]] = {}

# 🕵️ Espionage
kingdom_spies: Dict[int, Dict] = {}
spy_missions: Dict[int, List[Dict]] = {}

# ⚙️ Global Settings Cache
global_game_settings: Dict[str, Any] = {}

# ---------------------------------------------------
# 🔄 Live Game Setting Loader (from DB)
# ---------------------------------------------------

try:
    from sqlalchemy import text

    from .database import SessionLocal
except ImportError:  # When SQLAlchemy is not available in testing

    def text(q: str) -> str:  # type: ignore
        """Fallback text() implementation when SQLAlchemy is missing."""
        return q

    SessionLocal = None  # type: ignore


def load_game_settings() -> None:
    """
    Load all active global settings from the database into memory.
    These influence game-wide behaviors and can be modified dynamically.
    """
    if not SessionLocal:
        logger.warning("SessionLocal not initialized. Skipping game settings load.")
        return

    query = text(
        """
        SELECT gs.setting_key, gsv.setting_value
        FROM game_settings gs
        LEFT JOIN game_setting_values gsv
            ON gs.setting_key = gsv.setting_key
        WHERE gs.is_active = true
        """
    )

    try:
        with SessionLocal() as session:
            rows = session.execute(query).fetchall()
            # Build the settings dict in one step for efficiency
            global_game_settings.clear()
            global_game_settings.update({key: value for key, value in rows})
        logger.info("✅ Loaded %s game settings.", len(global_game_settings))
    except Exception as exc:
        logger.error("❌ Failed to load game settings.")
        logger.exception(exc)
