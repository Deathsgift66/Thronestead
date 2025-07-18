# Project Name: Thronestead©
# File Name: test_login_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
import json

import pytest
import time
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


class DummyRequest:
    def __init__(self, host="1.1.1.1", headers=None):
        self.client = type("c", (), {"host": host})
        self.headers = headers or {}


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
        self.updated = False

    def execute(self, query, *args, **kwargs):
        if "UPDATE users SET last_login_at" in str(query):
            self.updated = True
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
    assert db.updated is True


def test_login_status_missing():
    db = DummyDB(None)
    result = login_routes.login_status(user_id="u1", db=db)
    assert result["setup_complete"] is False
    assert db.updated is True

# ---- authenticate endpoint tests ----

class DummyClientAuth:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.auth = self
        self.inserted = None

    def sign_in_with_password(self, *_args, **_kwargs):
        if self.mode == "error":
            return {"error": {"message": "bad"}}
        if self.mode == "fail":
            raise Exception("fail")
        return {
            "session": {"access_token": "token"},
            "user": {"id": "u1", "confirmed_at": "now"},
        }

    def get_user(self, token):
        if self.mode == "invalid_session":
            return {"error": "bad"}
        return {"id": "u1"}

    def table(self, name):
        assert name == "user_active_sessions"

        class T:
            def __init__(self, parent):
                self.parent = parent

            def insert(self, data):
                self.parent.inserted = data
                return self

            def execute(self):
                return {}

        return T(self)


class DummyDBAuth:
    def __init__(self, deleted=False, status="active"):
        self.updated = False
        self.deleted = deleted
        self.status = status

    def execute(self, query, params=None):
        q = str(query).lower()
        if "update users set last_login_at" in q:
            self.updated = True
        if "from system_flags" in q:
            return type("R", (), {"fetchone": lambda _s: ("false",)})()
        class R:
            def fetchone(self_inner):
                if "from users" in q:
                    return (
                        "name",
                        1,
                        2,
                        True,
                        self.deleted,
                        self.status,
                    )
                return None

        return R()


def test_authenticate_success():
    client = DummyClientAuth()
    login_routes.get_supabase_client = lambda: client
    captured = {}
    login_routes.notify_new_login = lambda _db, uid, ip, dev: captured.update(
        {"uid": uid, "ip": ip, "dev": dev}
    )
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(
        email="e@example.com", password="p", remember=True
    )
    req = DummyRequest(headers={"User-Agent": "UA"})
    resp = DummyResponse()
    res = login_routes.authenticate(req, payload, response=resp, db=db)
    assert res["access_token"] == "token"
    assert resp.cookies.get("session_token") and resp.cookies["session_token"]["value"] == "token"
    assert res["username"] == "name"
    assert res["kingdom_id"] == 1
    assert res["alliance_id"] == 2
    assert res["setup_complete"] is True
    assert db.updated is True
    assert client.inserted["ip_address"] == "1.1.1.1"
    assert client.inserted["device_info"] == "UA"
    assert captured["uid"] == "u1"
    assert captured["ip"] == "1.1.1.1"
    assert captured["dev"] == "UA"


def test_authenticate_invalid():
    login_routes.get_supabase_client = lambda: DummyClientAuth("error")
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    req = DummyRequest()
    resp = DummyResponse()
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert exc.value.status_code == 401


def test_authenticate_invalid_session():
    login_routes.get_supabase_client = lambda: DummyClientAuth("invalid_session")
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    req = DummyRequest()
    resp = DummyResponse()
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert exc.value.status_code == 401


def test_authenticate_failure():
    login_routes.get_supabase_client = lambda: DummyClientAuth("fail")
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    req = DummyRequest()
    resp = DummyResponse()
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert exc.value.status_code == 503


def test_authenticate_disabled_by_flag():
    login_routes.get_supabase_client = lambda: DummyClientAuth()

    class FlagDB(DummyDBAuth):
        def execute(self, query, params=None):
            if "from system_flags" in str(query).lower():
                return type("R", (), {"fetchone": lambda _s: ("true",)})()
            return super().execute(query, params)

    db = FlagDB()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    req = DummyRequest()
    resp = DummyResponse()
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert exc.value.status_code == 503


def test_authenticate_deleted_account():
    login_routes.get_supabase_client = lambda: DummyClientAuth()
    db = DummyDBAuth(deleted=True)
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    req = DummyRequest()
    resp = DummyResponse()
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert exc.value.status_code == 403


def test_authenticate_backoff(monkeypatch):
    login_routes.get_supabase_client = lambda: DummyClientAuth("error")
    login_routes.FAILED_LOGINS.clear()
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    req = DummyRequest()
    resp = DummyResponse()
    with pytest.raises(HTTPException):
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert ("e@example.com", "1.1.1.1") in login_routes.FAILED_LOGINS
    login_routes.FAILED_LOGINS[("e@example.com", "1.1.1.1")] = (
        3,
        time.time() + 10,
    )
    with pytest.raises(HTTPException) as exc2:
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert exc2.value.status_code == 429


class DummyDBAttempt:
    def __init__(self, uid=None):
        self.uid = uid
        self.logged = None

    def execute(self, query, params):
        if "SELECT user_id" in str(query):
            class R:
                def fetchone(self_inner):
                    return (self.uid,) if self.uid else None

            return R()

    def commit(self):
        pass



# ---- reauthenticate endpoint tests ----

class DummyReauthClient:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.auth = self

    def sign_in_with_password(self, *_args, **_kwargs):
        if self.mode == "error":
            return {"error": "bad"}
        if self.mode == "fail":
            raise Exception("fail")
        return {"session": "token"}


class DummyDBReauth:
    def __init__(self, status="active"):
        self.status = status


def test_authenticate_supabase_unavailable():
    def raise_err():
        raise RuntimeError("no client")

    login_routes.get_supabase_client = raise_err
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    req = DummyRequest()
    resp = DummyResponse()
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(req, payload, response=resp, db=db)
    assert exc.value.status_code == 503
