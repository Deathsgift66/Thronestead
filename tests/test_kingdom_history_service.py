# Project Name: Thronestead©
# File Name: test_kingdom_history_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from services.kingdom_history_service import log_event, fetch_history, fetch_full_history

class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def mappings(self):
        return self

class DummyDB:
    def __init__(self):
        self.inserts = []
        self.select_rows = []
        self.calls = []

    def execute(self, query, params=None):
        q = str(query)
        params = params or {}
        self.calls.append(q)
        if q.strip().startswith("INSERT INTO kingdom_history_log"):
            self.inserts.append(params)
            return DummyResult()
        if "FROM kingdom_history_log" in q:
            return DummyResult(rows=self.select_rows)
        if "FROM kingdoms" in q:
            return DummyResult(row={"kingdom_name": "Demo"})
        if "FROM wars" in q:
            return DummyResult(rows=[{"war_id": 1}])
        if "FROM kingdom_achievements" in q:
            return DummyResult(rows=[{"achievement_code": "A"}])
        if "FROM kingdom_titles" in q:
            return DummyResult(rows=[{"title": "Hero"}])
        if "FROM kingdom_research_tracking" in q:
            return DummyResult(rows=[{"tech_code": "t1"}])
        if "FROM quest_kingdom_tracking" in q:
            return DummyResult(rows=[{"quest_code": "q1"}])
        if "FROM training_history" in q:
            return DummyResult(rows=[{"unit_name": "Archer"}])
        if "FROM projects_player" in q:
            return DummyResult(rows=[{"project_code": "p1"}])
        return DummyResult()

    def commit(self):
        pass

def test_log_event_inserts():
    db = DummyDB()
    log_event(db, 1, "build_complete", "Built Barracks")
    assert len(db.inserts) == 1
    assert db.inserts[0]["kid"] == 1
    assert db.inserts[0]["etype"] == "build_complete"


def test_fetch_history_returns_rows():
    db = DummyDB()
    db.select_rows = [(1, "war_victory", "Defeated", "2025-01-01")]
    logs = fetch_history(db, 1, 10)
    assert len(logs) == 1
    assert logs[0]["event_type"] == "war_victory"


def test_fetch_full_history_structure():
    db = DummyDB()
    result = fetch_full_history(db, 1)
    assert result["core"]["kingdom_name"] == "Demo"
    assert result["wars_fought"][0]["war_id"] == 1
