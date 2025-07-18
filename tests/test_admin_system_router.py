import pytest
from backend.routers import admin_system
from fastapi import HTTPException


class DummyResult:
    def __init__(self):
        pass

    def fetchone(self):
        return (True,)

    def fetchall(self):
        return []


class DummyDB:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((str(query), params))
        # Simulate admin check
        if str(query).strip().lower().startswith("select is_admin"):
            return DummyResult()
        return DummyResult()

    def commit(self):
        pass


def test_rollback_system_checks_password(monkeypatch):
    db = DummyDB()
    monkeypatch.setenv("MASTER_ROLLBACK_PASSWORD", "secret")
    res = admin_system.rollback_system(
        admin_system.RollbackPayload(password="secret"),
        admin_user_id="a1",
        db=db,
    )
    assert res["status"] == "rollback_triggered"
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_rollback_system_bad_password(monkeypatch):
    db = DummyDB()
    monkeypatch.setenv("MASTER_ROLLBACK_PASSWORD", "secret")
    with pytest.raises(HTTPException):
        admin_system.rollback_system(
            admin_system.RollbackPayload(password="wrong"),
            admin_user_id="a1",
            db=db,
        )
