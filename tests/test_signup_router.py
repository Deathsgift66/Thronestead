# Project Name: Thronestead©
# File Name: test_signup_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from fastapi import HTTPException
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from backend.db_base import Base
from backend.models import Kingdom, KingdomVipStatus, User
from sqlalchemy import text
from backend.routers import signup
from fastapi import Request




class DummyAuth:
    def __init__(self, user_id="u1", error=False, error_resp=False, resend_error=False):
        self._user_id = user_id
        self._error = error
        self._error_resp = error_resp
        self._resend_error = resend_error

    def sign_up(self, *_args, **_kwargs):
        if self._error:
            raise Exception("fail")
        if self._error_resp:
            return {"error": {"message": "bad"}}
        return {"user": {"id": self._user_id}}

    def resend(self, *_args, **_kwargs):
        if self._resend_error:
            raise Exception("fail")
        return {"status": "sent"}


class DummyClient:
    def __init__(self, user_id="u1", error=False, error_resp=False, resend_error=False):
        self.auth = DummyAuth(user_id, error, error_resp, resend_error)


def make_request():
    return Request({"type": "http", "method": "POST", "path": "/", "client": ("test", 0), "headers": []})


def test_register_creates_user_row(db_session):
    signup.get_supabase_client = lambda: DummyClient("newid")
    payload = signup.RegisterPayload(
        email="e@example.com",
        password="pass",
        username="user",
        kingdom_name="Realm",
        display_name="user",
        captcha_token="t",
    )
    res = signup.register(make_request(), payload, db=db_session)
    assert res["user_id"] == "newid"
    assert res["kingdom_id"] == 1
    user = db_session.query(User).get("newid")
    kingdom = db_session.query(Kingdom).get(1)
    vip = db_session.query(KingdomVipStatus).get("newid")
    res_row = db_session.execute(
        text("SELECT 1 FROM kingdom_resources WHERE kingdom_id = 1")
    ).fetchone()
    title_row = db_session.execute(
        text("SELECT title FROM kingdom_titles WHERE kingdom_id = 1")
    ).fetchone()
    assert user.email == "e@example.com"
    assert kingdom.kingdom_name == "Realm"
    assert vip.vip_level == 0
    assert user.sign_up_ip == "test"
    assert res_row is not None
    assert title_row is not None


def test_register_handles_error(db_session):
    signup.get_supabase_client = lambda: DummyClient(error=True)
    payload = signup.RegisterPayload(
        email="x@x.com",
        password="p",
        username="u",
        kingdom_name="k",
        display_name="u",
        captcha_token="t",
    )
    try:
        signup.register(make_request(), payload, db=db_session)
    except HTTPException as e:
        assert e.status_code == 500
    else:
        assert False


def test_register_returns_supabase_error(db_session):
    signup.get_supabase_client = lambda: DummyClient(error_resp=True)
    payload = signup.RegisterPayload(
        email="x@x.com",
        password="p",
        username="u",
        kingdom_name="k",
        display_name="u",
        captcha_token="t",
    )
    try:
        signup.register(make_request(), payload, db=db_session)
    except HTTPException as e:
        assert e.status_code == 400
    else:
        assert False


def test_register_invalid_username(db_session):
    signup.get_supabase_client = lambda: DummyClient("id")
    payload = signup.RegisterPayload(
        email="x@x.com",
        password="p",
        username="bad!name",
        kingdom_name="k",
        display_name="u",
        captcha_token="t",
    )
    with pytest.raises(HTTPException):
        signup.register(make_request(), payload, db=db_session)


def test_register_reserved_username(db_session):
    signup.get_supabase_client = lambda: DummyClient("id")
    with pytest.raises(ValueError):
        signup.RegisterPayload(
            email="x@x.com",
            password="p",
            username="Admin",
            kingdom_name="k",
            display_name="u",
            captcha_token="t",
        )


def test_register_captcha_failure(db_session):
    signup.get_supabase_client = lambda: DummyClient("id")

    def fail_captcha(*_args, **_kwargs):
        return False

    signup.verify_hcaptcha = fail_captcha

    payload = signup.RegisterPayload(
        email="x@x.com",
        password="p",
        username="usera",
        kingdom_name="k",
        display_name="u",
        captcha_token="bad",
    )
    with pytest.raises(HTTPException) as exc:
        signup.register(make_request(), payload, db=db_session)
    assert exc.value.status_code == 400


def test_register_with_existing_user(db_session):
    called = {"flag": False}

    class StubAuth(DummyAuth):
        def sign_up(self, *_args, **_kwargs):
            called["flag"] = True
            return {"user": {"id": "should-not"}}

    signup.get_supabase_client = lambda: type("C", (), {"auth": StubAuth()})()
    payload = signup.RegisterPayload(
        user_id="provided",
        email="e2@example.com",
        password="pass",
        username="user2",
        kingdom_name="Realm2",
        display_name="user2",
        captcha_token="t",
    )
    res = signup.register(make_request(), payload, db=db_session)
    assert res["user_id"] == "provided"
    assert called["flag"] is False


def test_resend_confirmation_success():
    signup.get_supabase_client = lambda: DummyClient()
    payload = signup.ResendPayload(email="e@example.com")
    res = signup.resend_confirmation(payload)
    assert res["status"] == "sent"


def test_resend_confirmation_error():
    signup.get_supabase_client = lambda: DummyClient(resend_error=True)
    payload = signup.ResendPayload(email="x@example.com")
    with pytest.raises(HTTPException):
        signup.resend_confirmation(payload)


def test_finalize_signup_creates_rows(db_session):
    payload = signup.FinalizePayload(
        user_id="fin1",
        username="finuser",
        display_name="finuser",
        kingdom_name="FinRealm",
        email="fin@example.com",
    )
    res = signup.finalize_signup(payload, db=db_session)
    assert res["status"] == "created"
    assert res["user_id"] == "fin1"
    assert res["kingdom_id"] == 1
    user = db_session.query(User).get("fin1")
    kingdom = db_session.query(Kingdom).get(1)
    res_row = db_session.execute(
        text("SELECT 1 FROM kingdom_resources WHERE kingdom_id = 1")
    ).fetchone()
    title_row = db_session.execute(
        text("SELECT title FROM kingdom_titles WHERE kingdom_id = 1")
    ).fetchone()
    assert user is not None
    assert kingdom.kingdom_name == "FinRealm"
    assert res_row is not None
    assert title_row is not None


def test_finalize_signup_conflict_username(db_session):
    payload = signup.FinalizePayload(
        user_id="dup1",
        username="dupuser",
        display_name="dup",
        kingdom_name="KingA",
        email="d1@example.com",
    )
    signup.finalize_signup(payload, db=db_session)

    payload2 = signup.FinalizePayload(
        user_id="dup2",
        username="dupuser",
        display_name="dup2",
        kingdom_name="KingB",
        email="d2@example.com",
    )
    with pytest.raises(HTTPException) as exc:
        signup.finalize_signup(payload2, db=db_session)
    assert exc.value.status_code == 409


def test_finalize_signup_conflict_kingdom(db_session):
    payload = signup.FinalizePayload(
        user_id="dup3",
        username="user3",
        display_name="u3",
        kingdom_name="SameKing",
        email="e3@example.com",
    )
    signup.finalize_signup(payload, db=db_session)

    payload2 = signup.FinalizePayload(
        user_id="dup4",
        username="user4",
        display_name="u4",
        kingdom_name="SameKing",
        email="e4@example.com",
    )
    with pytest.raises(HTTPException) as exc:
        signup.finalize_signup(payload2, db=db_session)
    assert exc.value.status_code == 409


class TableStub:
    def __init__(self, table):
        self.table = table
        self.eq_col = None
        self.value = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, col, value):
        self.eq_col = col
        self.value = value
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.table == "kingdoms" and self.value == "taken":
            return {"data": [{"id": 1}]}
        if self.table == "users":
            if self.eq_col == "username" and self.value == "taken":
                return {"data": [{"id": 1}]}
            if self.eq_col == "email" and self.value == "taken@example.com":
                return {"data": [{"id": 1}]}
        return {"data": []}


class AvailClient:
    def table(self, name):
        return TableStub(name)


def test_check_availability(db_session):
    signup.get_supabase_client = AvailClient
    payload = signup.CheckPayload(
        kingdom_name="taken",
        username="taken",
        email="taken@example.com",
    )
    res = signup.check_availability(payload, db=db_session)
    assert not res["kingdom_available"]
    assert not res["username_available"]
    assert not res["email_available"]


def test_check_availability_supabase_error(db_session):
    class ErrorTable:
        def select(self, *_args, **_kwargs):
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def execute(self):
            raise Exception("fail")

    class ErrorClient:
        def table(self, _name):
            return ErrorTable()

    signup.get_supabase_client = ErrorClient

    db_session.execute(
        text(
            "INSERT INTO users (user_id, username, display_name, kingdom_name, email)"
            " VALUES ('u1', 'dup', 'dup', 'Dup', 'dup@example.com')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO kingdoms (kingdom_id, user_id, kingdom_name, ruler_name)"
            " VALUES (1, 'u1', 'Dup', 'dup')"
        )
    )
    db_session.commit()

    payload = signup.CheckPayload(
        kingdom_name="Dup",
        username="dup",
        email="dup@example.com",
    )
    res = signup.check_availability(payload, db=db_session)
    assert not res["kingdom_available"]
    assert not res["username_available"]
    assert not res["email_available"]


def test_check_kingdom_name():
    signup.get_supabase_client = AvailClient
    res = signup.check_kingdom_name("taken")
    assert not res["available"]
    res = signup.check_kingdom_name("open")
    assert res["available"]
