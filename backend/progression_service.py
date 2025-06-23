# Project Name: Thronestead©
# File Name: progression_service.py
# Version: 6.14.2025.20.30
# Developer: Deathsgift66

"""In-memory progression logic used primarily for tests.

This module tracks castle XP, nobles and knights for a single kingdom without
requiring a database. All operations are protected by a :class:`threading.Lock`
so that concurrent test scenarios behave predictably.
"""

import logging
from threading import Lock
from typing import Dict, Set

logger = logging.getLogger("Thronestead.Progression")

# Global lock to ensure thread-safe updates when used in async tests
_state_lock = Lock()

# ---------------------------
# 🏰 Castle Progression State
# ---------------------------
castle_state: Dict[str, int] = {"level": 1}

# 🧙 Nobles Set for O(1) lookups
nobles: Set[str] = set()

# ⚔️ Knights Dictionary (id → data)
knights: Dict[str, Dict[str, int]] = {}


# ---------------------------
# 🏗️ Castle Progression Logic
# ---------------------------
def progress_castle() -> int:
    """Increase the castle level by one."""
    with _state_lock:
        castle_state["level"] += 1
        logger.info("🏰 Castle leveled up! New level: %s", castle_state["level"])
    return castle_state["level"]


# ---------------------------
# 👑 Noble Management
# ---------------------------
def add_noble(name: str) -> None:
    """Add a noble to the kingdom if not already present."""
    with _state_lock:
        if name not in nobles:
            nobles.add(name)
            logger.info("👑 Noble '%s' added.", name)
        else:
            logger.debug("Noble '%s' already exists.", name)


def remove_noble(name: str) -> None:
    """Remove a noble if they exist."""
    with _state_lock:
        if name in nobles:
            nobles.discard(name)
            logger.info("❌ Noble '%s' removed.", name)
        else:
            logger.debug("Noble '%s' not found.", name)


# ---------------------------
# 🛡️ Knight Promotion System
# ---------------------------
def add_knight(knight_id: str, rank: int = 1) -> None:
    """Register a new knight."""
    with _state_lock:
        if knight_id not in knights:
            knights[knight_id] = {"rank": rank}
            logger.info("🛡️ Knight '%s' added with rank %s.", knight_id, rank)
        else:
            logger.debug("Knight '%s' already exists.", knight_id)


def promote_knight(knight_id: str) -> int:
    """
    Promote a knight to the next rank.

    Returns:
        int: New rank after promotion
    """
    with _state_lock:
        if knight_id not in knights:
            logger.error("⚠️ Cannot promote: Knight '%s' not found.", knight_id)
            raise ValueError("Knight not found")

        knights[knight_id]["rank"] += 1
        new_rank = knights[knight_id]["rank"]
        logger.info("⬆️ Knight '%s' promoted to rank %s.", knight_id, new_rank)
        return new_rank


# ---------------------------
# 🔄 State Utilities
# ---------------------------
def get_state() -> Dict[str, object]:
    """Return a snapshot of the current progression state."""
    with _state_lock:
        return {
            "castle": castle_state.copy(),
            "nobles": set(nobles),
            "knights": {k: v.copy() for k, v in knights.items()},
        }


def reset_state() -> None:
    """Reset all progression data. Useful for tests."""
    with _state_lock:
        castle_state.update({"level": 1})
        nobles.clear()
        knights.clear()
