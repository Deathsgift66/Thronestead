# Project Name: Thronestead©
# File Name: manager.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Manages all active wars and coordinates battle ticks in Thronestead©.
Used as the backend executor for hourly tick engines and live battle resolutions.
"""

import logging
from threading import Lock
from typing import Dict, List, Optional

from ..database import SessionLocal
from services.system_flag_service import get_flag

from .engine import BattleTickHandler, WarState

logger = logging.getLogger("Thronestead.BattleManager")


class WarManager:
    """Thread-safe coordinator for active :class:`WarState` objects.

    Maintains war data and logs in memory while delegating tick
    execution to :class:`BattleTickHandler`. Access to internal
    structures is protected by a ``threading.Lock`` so multiple
    requests or background tasks can manipulate wars safely.
    """

    def __init__(self) -> None:
        """Initialize empty war tracking structures and tick handler."""
        self._active_wars: Dict[int, WarState] = {}
        self._war_logs: Dict[int, List[dict]] = {}
        self._lock = Lock()
        self.tick_handler = BattleTickHandler()

    def start_war(self, war: WarState) -> None:
        """Register a new war for real-time tick processing."""
        logger.info(f"⚔️ Starting war {war.war_id}")
        with self._lock:
            self._active_wars[war.war_id] = war
            self._war_logs[war.war_id] = []

    def run_combat_tick(self) -> None:
        """Advance all active wars by one tick and prune finished ones.

        This method is intentionally lightweight so it can be invoked
        regularly by a scheduler or HTTP endpoint. Completed wars are
        removed from memory to keep the manager scalable.
        """
        finished: List[int] = []
        with self._lock:
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
        with self._lock:
            return self._war_logs.get(war_id, [])

    def get_war(self, war_id: int) -> Optional[WarState]:
        """Retrieve the WarState instance for a given war."""
        with self._lock:
            return self._active_wars.get(war_id)


# 🔄 Shared instance used by API routes and tick engine
war_manager = WarManager()


def run_combat_tick() -> None:
    """
    Public entry point for the tick engine (e.g., hourly cron task).
    """
    if SessionLocal is not None:
        with SessionLocal() as db:
            if get_flag(db, "fallback_override"):
                logger.info("Fallback mode active, action delayed.")
                return
            war_manager.run_combat_tick()
    else:
        war_manager.run_combat_tick()
