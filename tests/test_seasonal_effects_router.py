# Project Name: Thronestead©
# File Name: test_seasonal_effects_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from backend.routers import seasonal_effects

class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self._single = False

    def select(self, *_args):
        return self

    def eq(self, *_args, **kwargs):
        return self

    def order(self, *_args, **kwargs):
        return self

    def limit(self, *_args):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._single:
            return {"data": self._data[0] if self._data else None}
        return {"data": self._data}

class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_seasonal_data_returns():
    curr = {"name": "Spring", "season_code": "SPR", "active": True}
    upcoming = [{"name": "Summer", "season_code": "SUM"}]
    seasonal_effects.get_supabase_client = lambda: DummyClient({"seasonal_effects": [curr] + upcoming})
    res = seasonal_effects.seasonal_data(user_id="u1")
    assert res["current"]["name"] == "Spring"
    assert len(res["forecast"]) == 2


def test_seasonal_data_missing():
    seasonal_effects.get_supabase_client = lambda: DummyClient({"seasonal_effects": []})
    try:
        seasonal_effects.seasonal_data(user_id="u1")
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False
