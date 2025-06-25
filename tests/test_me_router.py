import asyncio
import pytest
from fastapi import HTTPException

from backend.security import get_current_user
from backend.routers import me


class DummyAuth:
    def __init__(self, user):
        self.user = user
        self.called = None

    def get_user(self, token):
        self.called = token
        return self.user


class DummySupabase:
    def __init__(self, user):
        self.auth = DummyAuth(user)


def make_request(token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return type("Req", (), {"headers": headers})()


def test_get_current_user_success(monkeypatch):
    dummy = DummySupabase({"user": {"id": "u1"}})
    monkeypatch.setattr("backend.security.get_supabase_client", lambda: dummy)
    req = make_request("tok")
    user = asyncio.run(get_current_user(req))
    assert user["id"] == "u1"
    assert dummy.auth.called == "tok"


def test_get_current_user_missing():
    req = make_request()
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(req))


def test_get_current_user_invalid(monkeypatch):
    dummy = DummySupabase({"error": {"message": "bad"}})
    monkeypatch.setattr("backend.security.get_supabase_client", lambda: dummy)
    req = make_request("tok")
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(req))


def test_me_route_returns_user():
    result = asyncio.run(me.get_me(user={"id": "u1"}))
    assert result["id"] == "u1"
