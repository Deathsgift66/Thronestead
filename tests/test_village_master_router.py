# Project Name: Thronestead©
# File Name: test_village_master_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers import village_master

class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []
    def fetchall(self):
        return self._rows

class DummyDB:
    def __init__(self):
        self.queries = []
        self.rows = []
    def execute(self, query, params=None):
        self.queries.append((str(query), params))
        return DummyResult(self.rows)
    def commit(self):
        pass


def test_overview_filters_and_returns(monkeypatch):
    db = DummyDB()
    db.rows = [(1, "Village", 3, 9)]
    def fake_get_kingdom_id(db_arg, uid):
        assert db_arg is db
        assert uid == "u1"
        return 42
    monkeypatch.setattr(village_master, "get_kingdom_id", fake_get_kingdom_id)
    res = village_master.village_overview(user_id="u1", db=db)
    assert res["overview"][0]["building_count"] == 3
    assert db.queries[0][1]["kid"] == 42
