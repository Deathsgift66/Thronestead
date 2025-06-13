# Project Name: Kingmakers Rise©
# File Name: test_town_criers_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import pytest
from fastapi import HTTPException

from backend.routers import town_criers


class DummyTable:
    def __init__(self, rows=None):
        self._rows = rows or []
        self._single = False

    def select(self, *_):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def insert(self, payload):
        self._rows.append(payload)
        return self

    def execute(self):
        if self._single:
            return {"data": self._rows[0] if self._rows else None}
        return {"data": self._rows}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.setdefault(name, []))


def test_latest_invalid_user():
    client = DummyClient({"users": []})
    town_criers.get_supabase_client = lambda: client
    with pytest.raises(HTTPException):
        town_criers.latest_scrolls(user_id="u1")


def test_post_and_fetch():
    tables = {"users": [{"user_id": "u1", "display_name": "Tester"}]}
    client = DummyClient(tables)
    town_criers.get_supabase_client = lambda: client

    town_criers.post_scroll(town_criers.ScrollPayload(title="T", body="B"), user_id="u1")
    res = town_criers.latest_scrolls(user_id="u1")
    assert res["scrolls"][0]["title"] == "T"
