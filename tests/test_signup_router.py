# Project Name: Thronestead©
# File Name: test_signup_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import HTTPException
import pytest

from backend.db_base import Base
from backend.models import Kingdom, KingdomVipStatus, User
from backend.routers import signup
from fastapi import Request




class DummyAuth:
    def __init__(self, user_id="u1", error=False, error_resp=False):
        self._user_id = user_id
        self._error = error
        self._error_resp = error_resp

    def sign_up(self, *_args, **_kwargs):
        if self._error:
            raise Exception("fail")
        if self._error_resp:
            return {"error": {"message": "bad"}}
        return {"user": {"id": self._user_id}}


class DummyClient:
    def __init__(self, user_id="u1", error=False, error_resp=False):
        self.auth = DummyAuth(user_id, error, error_resp)


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
    )
    res = signup.register(make_request(), payload, db=db_session)
    assert res["user_id"] == "newid"
    assert res["kingdom_id"] == 1
    user = db_session.query(User).get("newid")
    kingdom = db_session.query(Kingdom).get(1)
    vip = db_session.query(KingdomVipStatus).get("newid")
    assert user.email == "e@example.com"
    assert kingdom.kingdom_name == "Realm"
    assert vip.vip_level == 0


def test_register_handles_error(db_session):
    signup.get_supabase_client = lambda: DummyClient(error=True)
    payload = signup.RegisterPayload(
        email="x@x.com",
        password="p",
        username="u",
        kingdom_name="k",
        display_name="u",
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
    )
    try:
        signup.register(make_request(), payload, db=db_session)
    except HTTPException as e:
        assert e.status_code == 400
    else:
        assert False
