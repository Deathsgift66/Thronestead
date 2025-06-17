# Project Name: Thronestead©
# File Name: test_kingdom_achievements_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers.kingdom_achievements import get_achievements

class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []
    def fetchone(self):
        return self._row
    def fetchall(self):
        return self._rows

class DummyDB:
    def __init__(self):
        self.rows = []
    def execute(self, query, params=None):
        q = str(query)
        if "FROM kingdoms" in q:
            return DummyResult((1,))
        if "FROM kingdom_achievement_catalogue" in q and "LEFT JOIN" in q:
            return DummyResult(rows=self.rows)
        return DummyResult()
    def commit(self):
        pass

def test_get_achievements_returns_rows():
    db = DummyDB()
    db.rows = [(
        "first",
        "First",
        "Desc",
        "military",
        {},
        5,
        False,
        "2025-01-01",
    )]
    result = get_achievements(user_id="u1", db=db)
    assert result["achievements"][0]["achievement_code"] == "first"
