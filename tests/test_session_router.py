import asyncio
import time

import pytest
from fastapi import HTTPException

from backend.routers import session


class DummyResponse:
    def __init__(self):
        self.cookies = {}

    def set_cookie(
        self,
        name,
        value,
        httponly=False,
        secure=False,
        samesite=None,
        path="/",
        domain=None,
    ):
        self.cookies[name] = {
            "value": value,
            "httponly": httponly,
            "secure": secure,
            "samesite": samesite,
            "path": path,
            "domain": domain,
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
    url = type("Url", (), {"hostname": "testhost"})()
    return type(
        "Req",
        (),
        {"headers": headers, "cookies": cookies, "url": url},
    )()


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
    req = make_request()
    result = session.store_session_cookie(
        session.TokenPayload(token="abc"), req, resp
    )
    assert result["stored"] is True
    c = resp.cookies.get("session_token")
    assert c and c["value"] == "abc"
    assert c["httponly"]
    assert c["secure"]
    assert c["samesite"] == "strict"
    assert c["path"] == "/api"
    assert c["domain"] == "testhost"


def test_fallback_validate_cached(monkeypatch):
    session.SESSION_CACHE.clear()
    monkeypatch.setattr(
        session,
        "decode_supabase_jwt",
        lambda _t: {"sub": "u1", "exp": time.time() + 60},
    )

    resp = DummyResponse()
    req = make_request("tok")
    session.store_session_cookie(session.TokenPayload(token="tok"), req, resp)

    class DummyDB:
        def execute(self, *_a, **_k):
            class R:
                def fetchone(self_inner):
                    return ("u1",)

            return R()

    result = session.fallback_validate(req, db=DummyDB())
    assert result["id"] == "u1"


def test_fallback_validate_db_rehydrate(monkeypatch):
    session.SESSION_CACHE.clear()
    monkeypatch.setattr(
        session,
        "decode_supabase_jwt",
        lambda _t: {"sub": "u2", "exp": time.time() + 60},
    )

    req = make_request("tok2")

    class DummyDB:
        def execute(self, query, params):
            q = str(query).lower()

            class R:
                def __init__(self, row):
                    self.row = row

                def fetchone(self_inner):
                    return self_inner.row

            if "from user_active_sessions" in q:
                return R(("s1",))
            return R((params.get("uid"),))

    db = DummyDB()
    result = session.fallback_validate(req, db=db)
    assert result["id"] == "u2"
    assert "tok2" in session.SESSION_CACHE


def test_fallback_validate_invalid(monkeypatch):
    session.SESSION_CACHE.clear()
    monkeypatch.setattr(
        session,
        "decode_supabase_jwt",
        lambda _t: {"sub": "u3", "exp": time.time() - 10},
    )

    req = make_request("tok3")

    class DummyDB:
        def execute(self, *_a, **_k):
            class R:
                def fetchone(self_inner):
                    return None

            return R()

    with pytest.raises(HTTPException):
        session.fallback_validate(req, db=DummyDB())

