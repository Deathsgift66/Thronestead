# Project Name: Thronestead©
# File Name: test_admin_dashboard_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
import pytest
from fastapi import HTTPException

from backend.routers import admin_dashboard


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class DummyDB:
    def __init__(self):
        self.queries = []
        self.rows = []

    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        lower = q.strip().lower()
        if lower.startswith("select is_admin"):
            return DummyResult([(True,)])
        if "from audit_log" in lower:
            return DummyResult(self.rows)
        if "from admin_alerts" in lower:
            return DummyResult(self.rows)
        return DummyResult()

    def commit(self):
        pass


def test_list_flags_returns_rows():
    db = DummyDB()
    db.rows = [("test", True)]
    flags = admin_dashboard.list_flags(admin_user_id="a1", db=db)
    assert flags[0]["flag_key"] == "test"


def test_get_audit_logs_with_dates():
    db = DummyDB()
    admin_dashboard.get_audit_logs(
        start_date="2025-01-01",
        end_date="2025-01-31",
        admin_user_id="a1",
        db=db,
    )
    joined = " ".join(db.queries[-1][0].lower().split())
    assert "created_at >=" in joined and "created_at <=" in joined


def test_get_audit_logs_returns_rows():
    db = DummyDB()
    db.rows = [(1, "u1", "login", "ok", "2025-01-01")]
    logs = admin_dashboard.get_audit_logs(db=db, admin_user_id="a1")
    assert len(logs) == 1
    assert logs[0]["action"] == "login"


def test_toggle_flag_updates_and_logs():
    db = DummyDB()
    admin_dashboard.toggle_flag("war_enabled", True, admin_user_id="a1", db=db)
    executed = " ".join(db.queries[1][0].split())
    assert "update system_flags" in executed.lower()
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_update_kingdom_field_runs_update():
    db = DummyDB()
    admin_dashboard.update_kingdom_field(1, "gold", 5, admin_user_id="a1", db=db)
    assert any("update kingdoms" in q[0].lower() for q in db.queries)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_update_field_payload_alias():
    db = DummyDB()
    payload = admin_dashboard.KingdomFieldUpdate(
        kingdom_id=2, field="motto", value="Hello"
    )
    admin_dashboard.update_field(payload, admin_user_id="a1", db=db)
    assert any("update kingdoms" in q[0].lower() for q in db.queries)


def test_get_flagged_users():
    db = DummyDB()
    db.rows = [("u1", "Exploit", "2025-01-02")]
    results = admin_dashboard.get_flagged_users(db=db, admin_user_id="a1")
    assert results[0]["alert_type"] == "Exploit"


def test_rollback_database_checks_password(monkeypatch):
    db = DummyDB()
    monkeypatch.setenv("MASTER_ROLLBACK_PASSWORD", "secret")
    admin_dashboard.rollback_database(
        admin_dashboard.RollbackRequest(password="secret"),
        admin_user_id="a1",
        db=db,
    )
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_rollback_database_bad_password(monkeypatch):
    db = DummyDB()
    monkeypatch.setenv("MASTER_ROLLBACK_PASSWORD", "secret")
    with pytest.raises(HTTPException):
        admin_dashboard.rollback_database(
            admin_dashboard.RollbackRequest(password="wrong"),
            admin_user_id="a1",
            db=db,
        )
