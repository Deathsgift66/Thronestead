# Project Name: Kingmakers Rise©
# File Name: test_progression_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import types
from backend.routers import progression_router as pr

class DummyResult:
    def __init__(self, row=None):
        self._row = row
    def fetchone(self):
        return self._row

class DummyDB:
    def __init__(self):
        self.calls = []
    def execute(self, query, params=None):
        q = str(query)
        self.calls.append((q, params))
        if "FROM kingdoms" in q:
            return DummyResult((1,))
        if "kingdom_castle_progression" in q:
            return DummyResult((3,))
        if "kingdom_nobles" in q:
            return DummyResult((2,))
        if "kingdom_knights" in q:
            return DummyResult((5,))
        if "kingdom_villages" in q:
            return DummyResult((3,))
        if "kingdom_troop_slots" in q:
            if "used_slots" in q:
                return DummyResult((6,))
        return DummyResult(None)
    def commit(self):
        pass

def test_progression_summary_returns_data():
    db = DummyDB()
    pr.calculate_troop_slots = lambda db, kid: 10
    result = pr.progression_summary(user_id="u1", db=db)
    assert result["castle_level"] == 3
    assert result["nobles_total"] == 2
    assert result["knights_total"] == 5
    assert result["troop_slots"]["used"] == 6
    assert result["troop_slots"]["available"] == 4
