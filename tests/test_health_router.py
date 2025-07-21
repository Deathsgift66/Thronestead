# Project Name: Thronestead©
# File Name: test_health_router.py
# Version: 7/1/2025 10:38
# Developer: Deathsgift66
"""Tests for the health router endpoints."""

from backend.routers import health


class DummyDB:
    def __init__(self, fail=False):
        self.fail = fail
        self.executed = False

    def execute(self, query, params=None):
        self.executed = True
        if self.fail:
            raise Exception("db failure")
        return None


def test_health_check_returns_ok():
    result = health.health_check()
    assert result == {"status": "ok"}


def test_database_health_success():
    db = DummyDB()
    result = health.database_health(db=db)
    assert result == {"status": "ok", "db": True}
    assert db.executed


def test_database_health_failure():
    db = DummyDB(fail=True)
    result = health.database_health(db=db)
    assert result == {"status": "error", "db": False}
    assert db.executed
