# Comment
# Project Name: Thronestead©
# File Name: test_region_router.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
from fastapi import HTTPException

from backend.routers import region


class DummyTable:
    def __init__(self, data=None, error=None):
        self._data = data or []
        self.error = error

    def select(self, *_args):
        return self

    def execute(self):
        if self.error:
            return {"error": self.error}
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return self.tables.get(name, DummyTable())


def test_get_regions_success():
    rows = [
        {
            "region_code": "north",
            "region_name": "North",
            "description": "cold",
            "wood_bonus": 1,
            "iron_bonus": 2,
            "troop_attack_bonus": 3,
        }
    ]
    client = DummyClient({"region_catalogue": DummyTable(data=rows)})
    region.get_supabase_client = lambda: client
    result = region.get_regions()
    assert result["regions"][0]["region_code"] == "north"


def test_get_regions_error():
    client = DummyClient({"region_catalogue": DummyTable(error="fail")})
    region.get_supabase_client = lambda: client
    try:
        region.get_regions()
    except HTTPException as e:
        assert e.status_code == 500
    else:
        assert False, "Expected HTTPException"
