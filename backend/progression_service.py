# Project Name: Kingmakers Rise©
# File Name: progression_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Handles castle leveling, noble management, and knight progression for Kingdoms.
This is an in-memory representation typically used for testing or simulation layers.
"""

from typing import Dict, List
import logging

logger = logging.getLogger("KingmakersRise.Progression")

# XP required to level up the castle
CASTLE_XP_THRESHOLD = 100

# ---------------------------
# 🏰 Castle Progression State
# ---------------------------
castle_state: Dict[str, int] = {
    "level": 1,
    "xp": 0,
}

# 🧙 Nobles List
nobles: List[str] = []

# ⚔️ Knights Dictionary (id → data)
knights: Dict[str, Dict[str, int]] = {}

# ---------------------------
# 🏗️ Castle Progression Logic
# ---------------------------
def progress_castle(xp_gain: int) -> int:
    """
    Increase castle XP and level up when threshold is reached.

    Args:
        xp_gain (int): Amount of XP gained

    Returns:
        int: New castle level
    """
    logger.debug(f"Adding {xp_gain} XP to castle (current XP: {castle_state['xp']})")
    castle_state["xp"] += xp_gain

    if castle_state["xp"] >= CASTLE_XP_THRESHOLD:
        castle_state["level"] += 1
        castle_state["xp"] = 0
        logger.info(f"🏰 Castle leveled up! New level: {castle_state['level']}")

    return castle_state["level"]

# ---------------------------
# 👑 Noble Management
# ---------------------------
def add_noble(name: str) -> None:
    """Add a noble to the kingdom if not already present."""
    if name not in nobles:
        nobles.append(name)
        logger.info(f"👑 Noble '{name}' added.")
    else:
        logger.debug(f"Noble '{name}' already exists.")

def remove_noble(name: str) -> None:
    """Remove a noble if they exist."""
    if name in nobles:
        nobles.remove(name)
        logger.info(f"❌ Noble '{name}' removed.")
    else:
        logger.debug(f"Noble '{name}' not found.")

# ---------------------------
# 🛡️ Knight Promotion System
# ---------------------------
def add_knight(knight_id: str, rank: int = 1) -> None:
    """Register a new knight."""
    if knight_id not in knights:
        knights[knight_id] = {"rank": rank}
        logger.info(f"🛡️ Knight '{knight_id}' added with rank {rank}.")
    else:
        logger.debug(f"Knight '{knight_id}' already exists.")

def promote_knight(knight_id: str) -> int:
    """
    Promote a knight to the next rank.

    Returns:
        int: New rank after promotion
    """
    if knight_id not in knights:
        logger.error(f"⚠️ Cannot promote: Knight '{knight_id}' not found.")
        raise ValueError("Knight not found")

    knights[knight_id]["rank"] += 1
    new_rank = knights[knight_id]["rank"]
    logger.info(f"⬆️ Knight '{knight_id}' promoted to rank {new_rank}.")
    return new_rank
