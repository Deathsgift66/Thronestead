from __future__ import annotations

from typing import Dict, List

from .engine import BattleTickHandler, WarState


class WarManager:
    """Manage active wars and run combat ticks."""

    def __init__(self) -> None:
        self._active_wars: Dict[int, WarState] = {}
        self._war_logs: Dict[int, List[dict]] = {}
        self.tick_handler = BattleTickHandler()

    def start_war(self, war: WarState) -> None:
        self._active_wars[war.war_id] = war
        self._war_logs[war.war_id] = []

    def run_combat_tick(self) -> None:
        """Process a tick for all active wars."""
        finished: List[int] = []
        for war_id, war in self._active_wars.items():
            logs = self.tick_handler.run_tick(war)
            self._war_logs[war_id].extend(logs)
            if war.castle_hp <= 0 or war.tick >= 12:
                finished.append(war_id)
        for war_id in finished:
            del self._active_wars[war_id]

    def get_logs(self, war_id: int) -> List[dict]:
        return self._war_logs.get(war_id, [])

    def get_war(self, war_id: int) -> WarState | None:
        return self._active_wars.get(war_id)


# Global manager instance used by API routers
war_manager = WarManager()


def run_combat_tick() -> None:
    """Entry point for the hourly tick engine."""
    war_manager.run_combat_tick()
