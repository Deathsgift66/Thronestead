from services.audit_service import log_action, fetch_logs


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
        if q.strip().startswith("INSERT INTO audit_log"):
            self.inserts.append(params)
            return DummyResult()
        if "FROM audit_log" in q:
            return DummyResult(self.select_rows)
        return DummyResult()

    def commit(self):
        pass


def test_log_action_inserts():
    db = DummyDB()
    log_action(db, "u1", "create_kingdom", "Created kingdom")
    assert len(db.inserts) == 1
    assert db.inserts[0]["uid"] == "u1"
    assert db.inserts[0]["act"] == "create_kingdom"


def test_fetch_logs_returns_rows():
    db = DummyDB()
    db.select_rows = [(1, "u1", "start_war", "vs 2", "2025-01-01")]
    logs = fetch_logs(db, "u1", 10)
    assert len(logs) == 1
    assert logs[0]["action"] == "start_war"
