# Project Name: Thronestead©
# File Name: test_vip_status_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from datetime import datetime, timedelta

from services.vip_status_service import upsert_vip_status, get_vip_status, is_vip_active


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.queries = []
        self.params = []
        self.row = None
        self.committed = False

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append(q)
        self.params.append(params)
        if q.startswith("SELECT vip_level"):
            return DummyResult(self.row)
        return DummyResult()

    def commit(self):
        self.committed = True


def test_upsert_vip_status_executes():
    db = DummyDB()
    upsert_vip_status(db, "u1", 1, datetime(2025, 7, 1))
    assert any("INSERT INTO kingdom_vip_status" in q for q in db.queries)
    assert db.committed


def test_get_vip_status_returns_record():
    db = DummyDB()
    exp = datetime.utcnow() + timedelta(days=1)
    db.row = (1, exp, False)
    record = get_vip_status(db, "u1")
    assert record["vip_level"] == 1
    assert record["expires_at"] == exp


def test_is_vip_active_founder():
    assert is_vip_active({"vip_level": 2, "expires_at": None, "founder": True})


def test_is_vip_active_expired():
    old = datetime.utcnow() - timedelta(days=1)
    record = {"vip_level": 1, "expires_at": old, "founder": False}
    assert not is_vip_active(record)
