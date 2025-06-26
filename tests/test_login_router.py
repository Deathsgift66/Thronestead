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


class DummyRequest:
    def __init__(self, host="1.1.1.1"):
        self.client = type("c", (), {"host": host})


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


# ---- authenticate endpoint tests ----

class DummyClientAuth:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.auth = self

    def sign_in_with_password(self, *_args, **_kwargs):
        if self.mode == "error":
            return {"error": {"message": "bad"}}
        if self.mode == "fail":
            raise Exception("fail")
        return {"session": "token", "user": {"id": "u1", "confirmed_at": "now"}}


class DummyDBAuth:
    def __init__(self):
        self.updated = False

    def execute(self, query, *args, **_kwargs):
        if "UPDATE users SET last_login_at" in str(query):
            self.updated = True
        class R:
            def fetchone(self):
                return ("name", 1, 2, True)

        return R()


def test_authenticate_success():
    login_routes.get_supabase_client = lambda: DummyClientAuth()
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    res = login_routes.authenticate(payload, db=db)
    assert res["session"] == "token"
    assert res["username"] == "name"
    assert res["kingdom_id"] == 1
    assert res["alliance_id"] == 2
    assert res["setup_complete"] is True
    assert db.updated is True


def test_authenticate_invalid():
    login_routes.get_supabase_client = lambda: DummyClientAuth("error")
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(payload, db=db)
    assert exc.value.status_code == 401


def test_authenticate_failure():
    login_routes.get_supabase_client = lambda: DummyClientAuth("fail")
    db = DummyDBAuth()
    payload = login_routes.AuthPayload(email="e@example.com", password="p")
    with pytest.raises(HTTPException) as exc:
        login_routes.authenticate(payload, db=db)
    assert exc.value.status_code == 500


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


def test_record_login_attempt_success():
    captured = {}

    def fake_log_action(_db, user_id, action, details):
        captured["uid"] = user_id
        captured["action"] = action

    login_routes.log_action = fake_log_action
    db = DummyDBAttempt(uid="u1")
    payload = login_routes.AttemptPayload(email="Test@Ex.com", success=True)
    req = DummyRequest()
    res = login_routes.record_login_attempt(req, payload, db=db)
    assert res["logged"] is True
    assert captured["uid"] == "u1"
    assert captured["action"] == "login_success"


def test_record_login_attempt_fail_no_user():
    captured = {}

    def fake_log_action(_db, user_id, action, details):
        captured["uid"] = user_id
        captured["action"] = action

    login_routes.log_action = fake_log_action
    db = DummyDBAttempt(uid=None)
    payload = login_routes.AttemptPayload(email="none@example.com", success=False)
    req = DummyRequest()
    res = login_routes.record_login_attempt(req, payload, db=db)
    assert res["logged"] is True
    assert captured["uid"] is None
    assert captured["action"] == "login_fail"
