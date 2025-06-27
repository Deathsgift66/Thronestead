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
        self.token = None

    def execute(self, query, params):
        q = str(query).lower()
        if "select email" in q:
            class R:
                def scalar(self_inner):
                    return self.email

            return R()
        if "insert into reauth_tokens" in q:
            self.token = params["tok"]
            class R:
                pass

            return R()
        if "delete from reauth_tokens" in q:
            return None
        raise AssertionError("unexpected query")

    def commit(self):
        pass


class DummyRequest:
    def __init__(self, host="1.1.1.1"):
        self.client = type("c", (), {"host": host})


def test_reauth_success(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient())
    reauth.FAILED_ATTEMPTS.clear()
    monkeypatch.setattr(reauth, "create_reauth_token", lambda _db, _u, ttl=300: "tok")
    monkeypatch.setattr(reauth, "log_action", lambda *_a, **_kw: None)
    db = DummyDB()
    payload = reauth.ReauthPayload(password="p")
    req = DummyRequest()
    res = reauth.reauthenticate(payload, req, user_id="u1", db=db)
    assert res["token"] == "tok"
    assert res["expires_in"] == reauth.TOKEN_TTL
    assert not reauth.FAILED_ATTEMPTS


def test_reauth_invalid(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient("error"))
    reauth.FAILED_ATTEMPTS.clear()
    monkeypatch.setattr(reauth, "create_reauth_token", lambda *_a, **_kw: "tok")
    monkeypatch.setattr(reauth, "log_action", lambda *_a, **_kw: None)
    db = DummyDB()
    payload = reauth.ReauthPayload(password="bad")
    req = DummyRequest()
    with pytest.raises(HTTPException) as exc:
        reauth.reauthenticate(payload, req, user_id="u1", db=db)
    assert exc.value.status_code == 401
    assert reauth.FAILED_ATTEMPTS[("u1", "1.1.1.1")][0] == 1


def test_reauth_lockout(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient("error"))
    reauth.FAILED_ATTEMPTS.clear()
    reauth.LOCKOUT_THRESHOLD = 1
    monkeypatch.setattr(reauth, "create_reauth_token", lambda *_a, **_kw: "tok")
    monkeypatch.setattr(reauth, "log_action", lambda *_a, **_kw: None)
    db = DummyDB()
    payload = reauth.ReauthPayload(password="bad")
    req = DummyRequest()
    with pytest.raises(HTTPException):
        reauth.reauthenticate(payload, req, user_id="u1", db=db)
    with pytest.raises(HTTPException) as exc:
        reauth.reauthenticate(payload, req, user_id="u1", db=db)
    assert exc.value.status_code == 429
