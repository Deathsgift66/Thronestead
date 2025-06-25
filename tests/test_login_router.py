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


class DummyDB:
    def __init__(self, row=None):
        self.row = row

    def execute(self, *_args, **_kwargs):
        class R:
            def __init__(self, row):
                self._row = row

            def fetchone(self):
                return self._row

        return R(self.row)


def test_login_status_true():
    db = DummyDB((True,))
    result = login_routes.login_status(user_id="u1", db=db)
    assert result["setup_complete"] is True


def test_login_status_missing():
    db = DummyDB(None)
    result = login_routes.login_status(user_id="u1", db=db)
    assert result["setup_complete"] is False

# New login endpoint tests
from backend.routers import login


class DummyAuth:
    def __init__(self, mode="ok"):
        self.mode = mode

    def sign_in_with_password(self, *_args, **_kwargs):
        if self.mode == "error":
            return {"error": {"message": "bad"}}
        if self.mode == "fail":
            raise Exception("fail")
        return {"session": "token"}


class DummyClientLogin:
    def __init__(self, mode="ok"):
        self.auth = DummyAuth(mode)


def test_login_user_success():
    login.get_supabase_client = lambda: DummyClientLogin()
    payload = login.LoginRequest(email="e@example.com", password="p")
    result = login.login_user(payload)
    assert result["session"] == "token"


def test_login_user_invalid_credentials():
    login.get_supabase_client = lambda: DummyClientLogin("error")
    payload = login.LoginRequest(email="e@example.com", password="p")
    with pytest.raises(HTTPException) as exc:
        login.login_user(payload)
    assert exc.value.status_code == 401
