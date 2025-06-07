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
