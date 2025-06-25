import asyncio

import pytest
from fastapi import HTTPException

from backend.routers import session


class DummyAuth:
    def __init__(self, user):
        self._user = user
        self.called_token = None

    def get_user(self, token):
        self.called_token = token
        return self._user


class DummySupabase:
    def __init__(self, user):
        self.auth = DummyAuth(user)


def make_request(token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return type("Req", (), {"headers": headers})()


def test_validate_success(monkeypatch):
    user_data = {"id": "u1"}
    dummy = DummySupabase(user_data)
    monkeypatch.setattr(session, "get_supabase_client", lambda: dummy)
    req = make_request("tok")
    result = asyncio.run(session.validate_session(req))
    assert result == user_data
    assert dummy.auth.called_token == "tok"


def test_missing_token():
    req = make_request()
    with pytest.raises(HTTPException) as exc:
        asyncio.run(session.validate_session(req))
    assert exc.value.status_code == 401


def test_invalid_token(monkeypatch):
    dummy = DummySupabase({"error": {"message": "bad"}})
    monkeypatch.setattr(session, "get_supabase_client", lambda: dummy)
    req = make_request("bad")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(session.validate_session(req))
    assert exc.value.status_code == 401

