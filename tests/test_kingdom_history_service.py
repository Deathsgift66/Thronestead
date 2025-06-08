from services.kingdom_history_service import log_event, fetch_history

class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows

class DummyDB:
    def __init__(self):
        self.inserts = []
        self.select_rows = []

    def execute(self, query, params=None):
        q = str(query)
        params = params or {}
        if q.strip().startswith("INSERT INTO kingdom_history_log"):
            self.inserts.append(params)
            return DummyResult()
        if "FROM kingdom_history_log" in q:
            return DummyResult(self.select_rows)
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
