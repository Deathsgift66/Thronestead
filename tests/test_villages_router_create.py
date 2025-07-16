from fastapi import HTTPException

import pytest
from fastapi import HTTPException

from backend.routers import villages_router
from backend.routers.villages_router import create_village, VillagePayload


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self, duplicate=False):
        self.duplicate = duplicate
        self.calls = []

    def execute(self, query, params=None):
        sql = str(query)
        self.calls.append((sql, params))
        if "SELECT 1 FROM kingdom_villages" in sql:
            return DummyResult((1,)) if self.duplicate else DummyResult(None)
        if "SELECT COUNT(*) FROM kingdom_villages" in sql:
            return DummyResult((0,))
        if "SELECT COUNT(*) FROM kingdom_nobles" in sql:
            return DummyResult((1,))
        if "INSERT INTO kingdom_villages" in sql:
            return DummyResult((1,))
        if "SELECT castle_level" in sql:
            return DummyResult((1,))
        return DummyResult(None)

    def commit(self):
        pass


def _fake_get_kid(db, uid):
    return 1


def test_create_village_invalid_name(monkeypatch):
    db = DummyDB()
    monkeypatch.setattr(villages_router, "get_kingdom_id", _fake_get_kid)
    with pytest.raises(HTTPException) as exc:
        create_village(VillagePayload(village_name="!!", village_type="economic"), user_id="u1", db=db)
    assert exc.value.status_code == 400


def test_create_village_duplicate(monkeypatch):
    db = DummyDB(duplicate=True)
    monkeypatch.setattr(villages_router, "get_kingdom_id", _fake_get_kid)
    with pytest.raises(HTTPException) as exc:
        create_village(VillagePayload(village_name="Town", village_type="economic"), user_id="u1", db=db)
    assert exc.value.status_code == 400


def test_create_village_success(monkeypatch):
    db = DummyDB()
    monkeypatch.setattr(villages_router, "get_kingdom_id", _fake_get_kid)
    res = create_village(VillagePayload(village_name="Town", village_type="economic"), user_id="u1", db=db)
    assert res["message"] == "Village created"
