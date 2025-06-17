# Project Name: Thronestead©
# File Name: test_progression_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from backend.progression_service import (
    progress_castle,
    add_noble,
    remove_noble,
    add_knight,
    promote_knight,
    castle_state,
    nobles,
    knights,
)
from services.progression_service import get_total_modifiers, calculate_troop_slots


def setup_function():
    castle_state["level"] = 1
    castle_state["xp"] = 0
    nobles.clear()
    knights.clear()


def test_progress_castle_level_up():
    level = progress_castle(50)
    assert level == 1
    assert castle_state["xp"] == 50

    level = progress_castle(60)
    assert level == 2
    assert castle_state["xp"] == 0


def test_noble_management():
    add_noble("Arthur")
    assert "Arthur" in nobles

    remove_noble("Arthur")
    assert "Arthur" not in nobles


def test_knight_management():
    add_knight("k1")
    assert knights["k1"]["rank"] == 1

    new_rank = promote_knight("k1")
    assert new_rank == 2
    assert knights["k1"]["rank"] == 2

    with pytest.raises(ValueError):
        promote_knight("missing")


def test_get_total_modifiers_default():
    class DummyResult:
        def __init__(self, row=None, rows=None):
            self._row = row
            self._rows = rows or []

        def fetchone(self):
            return self._row

        def fetchall(self):
            return self._rows

    class DummyDB:
        def execute(self, *args, **kwargs):
            return DummyResult()

    db = DummyDB()
    mods = get_total_modifiers(db, 1)
    assert mods == {
        "resource_bonus": {},
        "troop_bonus": {},
        "combat_bonus": {},
        "defense_bonus": {},
        "economic_bonus": {},
        "production_bonus": {},
    }


def test_calculate_troop_slots_includes_region_bonus():
    class DummyResult:
        def __init__(self, row=None):
            self._row = row

        def fetchone(self):
            return self._row

    class DummyDB:
        def execute(self, query, params=None):
            q = str(query)
            if "region_bonuses" in q:
                return DummyResult((10, 2, 1, 0, 0, 4))
            if "used_slots" in q:
                return DummyResult((0,))
            return DummyResult(None)

    total = calculate_troop_slots(DummyDB(), 1)
    assert total == 17
