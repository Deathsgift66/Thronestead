# Project Name: Kingmakers Rise©
# File Name: __init__.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66
"""
Kingmaker’s Rise: Progression Module

This package contains all models related to progression systems, including:
- Castle Leveling
- Nobles and Knights (Hero Units)
- Troop Slot Bonuses

Each component supports real-time scaling, tick-based updates, and ties into core kingdom logic.
"""

from .progression import (
    KingdomCastleProgression,
    KingdomNoble,
    KingdomKnight,
    TroopSlots,
)

__all__ = [
    "KingdomCastleProgression",
    "KingdomNoble",
    "KingdomKnight",
    "TroopSlots",
]
