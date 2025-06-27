import pytest
from fastapi import HTTPException
from sqlalchemy.sql import text

from backend.routers import reauth
from backend import security


class DummyClient:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.auth = self

    def sign_in_with_password(self, *_args, **_kwargs):
        if self.mode == "error":
            return {"error": {"message": "bad"}}
        if self.mode == "fail":
            raise Exception("fail")
        return {"session": "token"}


class DummyDB:
    def __init__(self, email="e@example.com"):
        self.email = email
        self.tokens = {}
        self.logs = []

    def execute(self, query, params=None):
        q = str(query).lower()
        params = params or {}
        if "select email, status" in q:
            class R:
                def fetchone(self_inner):
                    return (self.email, "active")
            return R()
        if "insert into reauth_tokens" in q:
            self.tokens[params["tok"]] = (params["uid"], params["exp"])
            return type("R", (), {})()
        if "delete from reauth_tokens" in q:
            if "expires_at" in q:
                now = params["now"]
                self.tokens = {t: (u, e) for t, (u, e) in self.tokens.items() if e > now}
            else:
                self.tokens.pop(params.get("tok"), None)
            return type("R", (), {})()
        if "select user_id, expires_at" in q:
            token = params["tok"]
            val = self.tokens.get(token)
            class R:
                def fetchone(self_inner):
                    return val
            return R()
        if "insert into audit_log" in q:
            self.logs.append(params)
            return type("R", (), {})()
        return type("R", (), {"fetchone": lambda self_inner: None})()

    def commit(self):
        pass


def make_request():
    return type("Req", (), {"client": type("c", (), {"host": "1.1.1.1"})})()


def test_reauth_success_token(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient())
    db = DummyDB()
    payload = reauth.ReauthPayload(password="p")
    res = reauth.reauthenticate(payload, make_request(), user_id="u1", db=db)
    assert res["reauthenticated"] is True
    assert res["token"] in db.tokens
    assert db.logs and db.logs[0]["act"] == "reauth_success"


def test_reauth_invalid_logs(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient("error"))
    db = DummyDB()
    payload = reauth.ReauthPayload(password="bad")
    with pytest.raises(HTTPException):
        reauth.reauthenticate(payload, make_request(), user_id="u1", db=db)
    assert db.logs and db.logs[0]["act"] == "reauth_fail"


def test_validate_reauth_token_expiry():
    db = DummyDB()
    db.tokens["tok"] = ("u1", "2000-01-01T00:00:00")
    with pytest.raises(HTTPException):
        security.validate_reauth_token("tok", db)
    assert "tok" not in db.tokens
