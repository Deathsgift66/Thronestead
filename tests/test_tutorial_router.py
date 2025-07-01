# Project Name: Thronestead©
# File Name: test_tutorial_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
import pytest
from fastapi import HTTPException

from backend.routers import tutorial


class DummyTable:
    def __init__(self, rows=None):
        self._rows = rows or []
        self._single = False

    def select(self, *_):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._single:
            return {"data": self._rows[0] if self._rows else None}
        return {"data": self._rows}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_invalid_user():
    client = DummyClient({"users": []})
    tutorial.get_supabase_client = lambda: client
    with pytest.raises(HTTPException):
        tutorial.steps(user_id="u1")


def test_returns_steps():
    rows = [{"id": 1, "title": "Intro", "description": "d", "step_number": 1}]
    tables = {"users": [{"user_id": "u1"}], "tutorial_steps": rows}
    client = DummyClient(tables)
    tutorial.get_supabase_client = lambda: client
    result = tutorial.steps(user_id="u1")
    assert result["steps"][0]["title"] == "Intro"
