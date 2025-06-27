import asyncio

import pytest
from fastapi import HTTPException

from backend.routers import session


class DummyResponse:
    def __init__(self):
        self.cookies = {}

    def set_cookie(self, name, value, httponly=False, secure=False, samesite=None):
        self.cookies[name] = {
            "value": value,
            "httponly": httponly,
            "secure": secure,
            "samesite": samesite,
        }


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
    cookies = {}
    if token:
        cookies["session_token"] = token
    return type("Req", (), {"headers": headers, "cookies": cookies})()


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


def test_store_cookie():
    resp = DummyResponse()
    result = session.store_session_cookie(session.TokenPayload(token="abc"), resp)
    assert result["stored"] is True
    c = resp.cookies.get("session_token")
    assert c and c["value"] == "abc"
    assert c["httponly"]
    assert c["secure"]
    assert c["samesite"] == "strict"

