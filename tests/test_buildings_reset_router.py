# Project Name: Thronestead©
# File Name: test_buildings_reset_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from fastapi import HTTPException

from backend.routers.buildings import BuildingActionPayload, reset_build


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row

    def mappings(self):
        return self


class DummyDB:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        q = str(query)
        self.calls.append((q, params))
        if "SELECT kingdom_id" in q:
            return DummyResult((1,))
        return DummyResult()

    def commit(self):
        pass


def test_reset_build_updates_level():
    db = DummyDB()
    payload = BuildingActionPayload(village_id=1, building_id=2)
    reset_build(payload, user_id="u1", db=db)
    executed = " ".join(db.calls[1][0].split()).lower()
    assert "update village_buildings" in executed
    assert "level = 0" in executed


def test_reset_build_forbidden():
    class ForbiddenDB(DummyDB):
        def execute(self, query, params=None):
            if "SELECT kingdom_id" in str(query):
                return DummyResult((2,))
            return super().execute(query, params)

    db = ForbiddenDB()
    try:
        reset_build(
            BuildingActionPayload(village_id=1, building_id=2), user_id="u1", db=db
        )
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False, "Expected HTTPException"
