# Project Name: Thronestead©
# File Name: test_login_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import json

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from backend.routers import login_routes


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args):
        return self

    def execute(self):
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_announcements_returned():
    rows = [
        {
            "id": 1,
            "title": "Welcome",
            "content": "Greetings",
            "created_at": "2025-01-01",
        }
    ]
    login_routes.get_supabase_client = lambda: DummyClient({"announcements": rows})
    resp = login_routes.get_announcements()
    assert isinstance(resp, JSONResponse)
    data = json.loads(resp.body.decode())
    assert data["announcements"][0]["title"] == "Welcome"


def test_supabase_unavailable_returns_503():
    def raise_error():
        raise RuntimeError("no client")

    login_routes.get_supabase_client = raise_error
    with pytest.raises(HTTPException) as exc:
        login_routes.get_announcements()
    assert exc.value.status_code == 503
