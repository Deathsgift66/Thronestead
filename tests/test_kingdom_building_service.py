# Project Name: Thronestead©
# File Name: test_kingdom_building_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import HTTPException
from services.kingdom_building_service import (
    construct_building,
    upgrade_building,
    mark_completed_buildings,
)


class DummyResult:
    def __init__(self, row=None, rowcount=0):
        self._row = row
        self.rowcount = rowcount

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self, select_row=None, rowcount=1):
        self.queries = []
        self.select_row = select_row
        self.rowcount = rowcount
        self.commits = 0

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append(q)
        if q.startswith("SELECT id, level FROM village_buildings"):
            return DummyResult(row=self.select_row)
        if "RETURNING id" in q:
            return DummyResult(row=(1,))
        return DummyResult(rowcount=self.rowcount)

    def commit(self):
        self.commits += 1


def test_construct_building_uses_under_construction():
    db = DummyDB()
    bid = construct_building(db, 1, 2, "u1", 60)
    assert bid == 1
    assert any("under_construction" in q for q in db.queries)
    assert db.commits == 1


def test_upgrade_building_sets_status():
    db = DummyDB(select_row=(5, 1))
    upgrade_building(db, 1, 2, "u1", 60)
    joined = " ".join(db.queries)
    assert "UPDATE village_buildings" in joined
    assert "under_construction" in joined
    assert db.commits == 1


def test_mark_completed_buildings_uses_under_construction():
    db = DummyDB(rowcount=2)
    count = mark_completed_buildings(db)
    assert count == 2
    joined = " ".join(db.queries)
    assert "construction_status = 'complete'" in joined
    assert "construction_status = 'under_construction'" in joined
    assert db.commits == 1
