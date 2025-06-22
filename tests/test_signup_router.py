# Project Name: Thronestead©
# File Name: test_signup_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.db_base import Base
from backend.models import User, Kingdom, KingdomVipStatus
from backend.routers import signup


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


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


def test_register_creates_user_row():
    Session = setup_db()
    db = Session()
    signup.get_supabase_client = lambda: DummyClient("newid")
    payload = signup.RegisterPayload(
        email="e@example.com",
        password="pass",
        username="user",
        kingdom_name="Realm",
        display_name="user",
    )
    res = signup.register(payload, db=db)
    assert res["user_id"] == "newid"
    assert res["kingdom_id"] == 1
    user = db.query(User).get("newid")
    kingdom = db.query(Kingdom).get(1)
    vip = db.query(KingdomVipStatus).get("newid")
    assert user.email == "e@example.com"
    assert kingdom.kingdom_name == "Realm"
    assert vip.vip_level == 0


def test_register_handles_error():
    Session = setup_db()
    db = Session()
    signup.get_supabase_client = lambda: DummyClient(error=True)
    payload = signup.RegisterPayload(
        email="x@x.com",
        password="p",
        username="u",
        kingdom_name="k",
        display_name="u",
    )
    try:
        signup.register(payload, db=db)
    except HTTPException as e:
        assert e.status_code == 500
    else:
        assert False


def test_register_returns_supabase_error():
    Session = setup_db()
    db = Session()
    signup.get_supabase_client = lambda: DummyClient(error_resp=True)
    payload = signup.RegisterPayload(
        email="x@x.com",
        password="p",
        username="u",
        kingdom_name="k",
        display_name="u",
    )
    try:
        signup.register(payload, db=db)
    except HTTPException as e:
        assert e.status_code == 400
    else:
        assert False
