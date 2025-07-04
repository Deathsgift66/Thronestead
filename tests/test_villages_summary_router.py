# Project Name: Thronestead©
# File Name: test_villages_summary_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from fastapi import HTTPException

from backend.routers.villages_router import get_village_summary


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def mappings(self):
        return self

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.calls = []
        self.rows = []

    def execute(self, query, params=None):
        self.calls.append((str(query), params))
        if "FROM kingdom_villages WHERE village_id" in str(
            query
        ) and "RETURNING" not in str(query):
            if "SELECT kingdom_id" in str(query):
                return DummyResult([(1,)])
            return DummyResult(
                [
                    {
                        "village_id": 1,
                        "village_name": "Rivertown",
                        "village_type": "economic",
                        "created_at": 0,
                    }
                ]
            )
        if "FROM village_resources" in str(query):
            return DummyResult([{"village_id": 1, "wood": 100}])
        if "FROM village_buildings" in str(query):
            return DummyResult([{"building_id": 1, "level": 2}])
        return DummyResult()


def test_get_village_summary_success():
    db = DummyDB()
    result = get_village_summary(1, user_id="u1", db=db)
    assert result["village"]["village_name"] == "Rivertown"
    assert result["resources"]["wood"] == 100
    assert result["buildings"][0]["level"] == 2


def test_get_village_summary_forbidden():
    class ForbiddenDB(DummyDB):
        def execute(self, query, params=None):
            if "SELECT kingdom_id" in str(query):
                return DummyResult([(2,)])
            return super().execute(query, params)

    db = ForbiddenDB()
    try:
        get_village_summary(1, user_id="u1", db=db)
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False, "Expected HTTPException"
