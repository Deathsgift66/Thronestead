# Project Name: Kingmakers Rise©
# File Name: manager.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Manages all active wars and coordinates battle ticks in Kingmakers Rise©.
Used as the backend executor for hourly tick engines and live battle resolutions.
"""

from typing import Dict, List, Optional
import logging

from .engine import BattleTickHandler, WarState

logger = logging.getLogger("KingmakersRise.BattleManager")


class WarManager:
    """
    Orchestrates active tactical wars.
    Tracks WarState instances and tick logs,
    applies tick processing via BattleTickHandler.
    """

    def __init__(self) -> None:
        self._active_wars: Dict[int, WarState] = {}
        self._war_logs: Dict[int, List[dict]] = {}
        self.tick_handler = BattleTickHandler()

    def start_war(self, war: WarState) -> None:
        """Register a new war for real-time tick processing."""
        logger.info(f"⚔️ Starting war {war.war_id}")
        self._active_wars[war.war_id] = war
        self._war_logs[war.war_id] = []

    def run_combat_tick(self) -> None:
        """
        Process a battle tick for every active war.

        Ends wars when:
        - Castle HP reaches 0
        - Max tick count (12) is exceeded
        """
        finished: List[int] = []

        for war_id, war in list(self._active_wars.items()):
            logger.debug(f"🔁 Running tick {war.tick} for war {war_id}")
            logs = self.tick_handler.run_tick(war)
            self._war_logs[war_id].extend(logs)

            if war.castle_hp <= 0:
                logger.info(f"🏰 War {war_id} ended — castle destroyed.")
                finished.append(war_id)
            elif war.tick >= 12:
                logger.info(f"⏱️ War {war_id} ended — tick limit reached.")
                finished.append(war_id)

        for war_id in finished:
            self._active_wars.pop(war_id, None)

    def get_logs(self, war_id: int) -> List[dict]:
        """Return all logs for a specific war ID."""
        return self._war_logs.get(war_id, [])

    def get_war(self, war_id: int) -> Optional[WarState]:
        """Retrieve the WarState instance for a given war."""
        return self._active_wars.get(war_id)


# 🔄 Shared instance used by API routes and tick engine
war_manager = WarManager()


def run_combat_tick() -> None:
    """
    Public entry point for the tick engine (e.g., hourly cron task).
    """
    war_manager.run_combat_tick()
