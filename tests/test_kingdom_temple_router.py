import pytest
from fastapi import HTTPException

from backend.routers import kingdom as kingdom_router
from backend.routers.kingdom import construct_temple, TemplePayload, MAX_SUB_TEMPLES

class DummyResult:
    def __init__(self, row=None):
        self._row = row
    def fetchone(self):
        return self._row
    def scalar(self):
        return self._row[0] if self._row else None

class DummyDB:
    def __init__(self):
        self.temples = []
        self.last_insert = None
    def execute(self, query, params=None):
        q = str(query).lower()
        if "select 1 from kingdom_temples" in q:
            exists = any(t.get("is_major") for t in self.temples)
            return DummyResult((1,) if exists else None)
        if "select count(*) from kingdom_temples" in q:
            count = sum(1 for t in self.temples if not t.get("is_major"))
            return DummyResult((count,))
        if q.strip().startswith("insert into kingdom_temples"):
            self.last_insert = params
            self.temples.append({
                "kingdom_id": params["kid"],
                "is_major": params["major"],
            })
            return DummyResult()
        return DummyResult()
    def commit(self):
        pass


def fake_get_kingdom_id(db, uid):
    return 1


def test_invalid_temple_type(monkeypatch):
    monkeypatch.setattr(kingdom_router, "get_kingdom_id", fake_get_kingdom_id)
    db = DummyDB()
    payload = TemplePayload(temple_type="Invalid")
    with pytest.raises(HTTPException) as exc:
        construct_temple(payload, user_id="u1", db=db)
    assert exc.value.status_code == 400


def test_major_temple_already_exists(monkeypatch):
    monkeypatch.setattr(kingdom_router, "get_kingdom_id", fake_get_kingdom_id)
    db = DummyDB()
    db.temples.append({"is_major": True})
    payload = TemplePayload(temple_type="Temple of Light", is_major=True)
    with pytest.raises(HTTPException) as exc:
        construct_temple(payload, user_id="u1", db=db)
    assert exc.value.status_code == 400


def test_sub_temple_limit(monkeypatch):
    monkeypatch.setattr(kingdom_router, "get_kingdom_id", fake_get_kingdom_id)
    db = DummyDB()
    for _ in range(MAX_SUB_TEMPLES):
        db.temples.append({"is_major": False})
    payload = TemplePayload(temple_type="Temple of War")
    with pytest.raises(HTTPException) as exc:
        construct_temple(payload, user_id="u1", db=db)
    assert exc.value.status_code == 400
