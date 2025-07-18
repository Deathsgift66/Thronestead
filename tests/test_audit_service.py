# Project Name: Thronestead©
# File Name: test_audit_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from services.audit_service import (
    fetch_filtered_logs,
    fetch_logs,
    fetch_user_related_logs,
    log_action,
    log_alliance_activity,
)


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.inserts = []
        self.select_rows = []
        self.queries = []

    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        if q.strip().startswith("INSERT INTO audit_log"):
            self.inserts.append(params)
            return DummyResult()
        if q.strip().startswith("INSERT INTO alliance_activity_log"):
            self.inserts.append(params)
            return DummyResult()
        if "FROM audit_log" in q:
            return DummyResult(self.select_rows)
        return DummyResult()

    def commit(self):
        pass


def test_log_action_inserts():
    db = DummyDB()
    log_action(db, "u1", "create_kingdom", "Created kingdom", "1.1.1.1", "UA", kingdom_id=5)
    assert len(db.inserts) == 1
    assert db.inserts[0]["uid"] == "u1"
    assert db.inserts[0]["act"] == "create_kingdom"
    assert db.inserts[0]["ip"] == "1.1.1.1"
    assert db.inserts[0]["dev"] == "UA"
    assert db.inserts[0]["kid"] == 5


def test_fetch_logs_returns_rows():
    db = DummyDB()
    db.select_rows = [(1, "u1", False, "start_war", "vs 2", "2025-01-01", 3)]
    logs = fetch_logs(db, "u1", 3, 10)
    assert len(logs) == 1
    assert logs[0]["action"] == "start_war"
    assert logs[0]["kingdom_id"] == 3


def test_log_alliance_activity_inserts():
    db = DummyDB()
    log_alliance_activity(db, 2, "u1", "Treaty Proposed", "Pact")
    assert any(p.get("aid") == 2 for p in db.inserts)


def test_fetch_filtered_logs_params():
    db = DummyDB()
    db.select_rows = [(1, "u1", False, "login", "success", "2025-01-01")]
    logs = fetch_filtered_logs(db, user_id="u1", action="log", limit=5, offset=10)
    assert len(logs) == 1
    q, params = db.queries[-1]
    assert params["uid"] == "u1"
    assert params["act"] == "%log%"
    assert params["limit"] == 5
    assert params["offset"] == 10


def test_fetch_logs_masks_deleted_user():
    db = DummyDB()
    db.select_rows = [(1, "u1", True, "ban", "Removed", "2025-01-01")]
    logs = fetch_logs(db, None, None, 10)
    assert logs[0]["user_id"] == "[deleted_user]"


def test_fetch_user_related_logs_keys():
    db = DummyDB()
    result = fetch_user_related_logs(db, "u2")
    assert set(result.keys()) >= {
        "global",
        "alliance",
        "vault",
        "grants",
        "loans",
        "training",
    }
