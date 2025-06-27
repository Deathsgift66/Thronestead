import pytest
from fastapi import HTTPException

from backend.routers import reauth


class DummyClient:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.called = False

    def sign_in_with_password(self, *_args, **_kwargs):
        self.called = True
        if self.mode == "error":
            return {"error": {"message": "bad"}}
        if self.mode == "fail":
            raise Exception("fail")
        return {"session": "token"}


class DummyDB:
    def __init__(self, email="e@example.com"):
        self.email = email

    def execute(self, query, params):
        class R:
            def scalar(self_inner):
                return self.email

        return R()


class DummyRequest:
    def __init__(self, host="1.1.1.1"):
        self.client = type("c", (), {"host": host})


def test_reauth_success(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient())
    reauth.REAUTH_TOKENS.clear()
    reauth.FAILED_ATTEMPTS.clear()
    db = DummyDB()
    payload = reauth.ReauthPayload(password="p")
    req = DummyRequest()
    res = reauth.reauthenticate(payload, req, user_id="u1", db=db)
    assert res["reauthenticated"] is True
    assert "u1" in reauth.REAUTH_TOKENS
    assert not reauth.FAILED_ATTEMPTS


def test_reauth_invalid(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient("error"))
    reauth.REAUTH_TOKENS.clear()
    reauth.FAILED_ATTEMPTS.clear()
    db = DummyDB()
    payload = reauth.ReauthPayload(password="bad")
    req = DummyRequest()
    with pytest.raises(HTTPException) as exc:
        reauth.reauthenticate(payload, req, user_id="u1", db=db)
    assert exc.value.status_code == 401
    assert reauth.FAILED_ATTEMPTS[("u1", "1.1.1.1")][0] == 1


def test_reauth_lockout(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient("error"))
    reauth.REAUTH_TOKENS.clear()
    reauth.FAILED_ATTEMPTS.clear()
    reauth.LOCKOUT_THRESHOLD = 1
    db = DummyDB()
    payload = reauth.ReauthPayload(password="bad")
    req = DummyRequest()
    with pytest.raises(HTTPException):
        reauth.reauthenticate(payload, req, user_id="u1", db=db)
    with pytest.raises(HTTPException) as exc:
        reauth.reauthenticate(payload, req, user_id="u1", db=db)
    assert exc.value.status_code == 429
