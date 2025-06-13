# Project Name: Kingmakers Rise©
# File Name: test_buildings_info_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers.buildings import get_building_info
from fastapi import HTTPException

class DummyResult:
    def __init__(self, row=None):
        self._row = row
    def mappings(self):
        return self
    def fetchone(self):
        return self._row

class DummyDB:
    def __init__(self, row=None):
        self.row = row
    def execute(self, query, params=None):
        return DummyResult(row=self.row)

def test_get_building_info_success():
    db = DummyDB(row={"building_id": 1, "building_name": "Farm"})
    result = get_building_info(1, user_id="u1", db=db)
    assert result["building"]["building_name"] == "Farm"

def test_get_building_info_not_found():
    db = DummyDB(row=None)
    try:
        get_building_info(99, user_id="u1", db=db)
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False, "Expected HTTPException"
