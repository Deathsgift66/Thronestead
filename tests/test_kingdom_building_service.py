import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.kingdom_building_service import upgrade_building, mark_completed_buildings
from fastapi import HTTPException

class DummyResult:
    def __init__(self, row=None, rowcount=0):
        self._row = row
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

class DummyDB:
    def __init__(self):
        self.queries = []
        self.commits = 0
        self.row_to_return = (1, 1)
        self.rowcount = 1

    def execute(self, query, params=None):
        q = str(query).lower().strip()
        self.queries.append(q)
        if q.startswith("select id, level from village_buildings"):
            return DummyResult(self.row_to_return)
        return DummyResult(rowcount=self.rowcount)

    def commit(self):
        self.commits += 1


def test_upgrade_building_does_not_change_level():
    db = DummyDB()
    upgrade_building(db, 1, 2, "u1", 60)
    update_query = db.queries[-1]
    assert "update village_buildings" in update_query
    assert "construction_status = 'in_progress'" in update_query
    assert "level" not in update_query
    assert db.commits == 1


def test_mark_completed_buildings_increments_level():
    db = DummyDB()
    count = mark_completed_buildings(db)
    assert count == 1
    update_query = db.queries[-1]
    assert "level = level + 1" in update_query
    assert db.commits == 1
