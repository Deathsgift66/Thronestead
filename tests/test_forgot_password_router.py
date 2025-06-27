# Project Name: Thronestead©
# File Name: test_forgot_password_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import hashlib
import time
import uuid
import pytest
from fastapi import HTTPException
from backend.models import Notification, User
from backend.routers import forgot_password as fp




def create_user(db):
    uid = str(uuid.uuid4())
    user = User(user_id=uid, username="t", display_name="t", email="e@example.com")
    db.add(user)
    db.commit()
    return uid


class DummyRequest:
    def __init__(self, host="1.1.1.1"):
        self.client = type("c", (), {"host": host})


def test_request_stores_token(db_session):
    uid = create_user(db_session)
    fp.RESET_STORE.clear()
    req = DummyRequest()
    fp.request_password_reset(fp.EmailPayload(email="e@example.com"), req, db_session)
    assert len(fp.RESET_STORE) == 1
    stored_uid = next(iter(fp.RESET_STORE.values()))[0]
    assert stored_uid == uid


def test_full_reset_flow(db_session):
    uid = create_user(db_session)
    fp.RESET_STORE.clear()
    fp.VERIFIED_SESSIONS.clear()
    token = "TESTTOKEN1234"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    fp.RESET_STORE[token_hash] = (uid, time.time() + 60)
    fp.verify_reset_code(fp.CodePayload(code=token))
    assert uid in fp.VERIFIED_SESSIONS
    fp.set_new_password(
        fp.PasswordPayload(
            code=token,
            new_password="StrongPass1234",
            confirm_password="StrongPass1234",
        ),
        db_session,
    )
    assert uid not in fp.VERIFIED_SESSIONS
    assert token_hash not in fp.RESET_STORE
    notif = db_session.query(Notification).filter(Notification.user_id == uid).first()
    assert notif is not None


def test_sign_out_called(db_session):
    uid = create_user(db_session)
    fp.RESET_STORE.clear()
    fp.VERIFIED_SESSIONS.clear()
    token = "tok"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    fp.RESET_STORE[token_hash] = (uid, time.time() + 60)

    called = {}

    class DummyAdmin:
        def update_user_by_id(self, uid_arg, data):
            called["update"] = uid_arg

        def sign_out_user(self, uid_arg, session_token=None):
            called["signout"] = (uid_arg, session_token)

    class DummySB:
        def __init__(self):
            self.auth = type("A", (), {"admin": DummyAdmin()})()

    fp.get_supabase_client = lambda: DummySB()

    fp.verify_reset_code(fp.CodePayload(code=token))
    fp.set_new_password(
        fp.PasswordPayload(code=token, new_password="StrongPass1234", confirm_password="StrongPass1234"),
        db_session,
    )

    assert called.get("update") == uid
    assert called.get("signout")[0] == uid


def test_keep_session_token(db_session):
    uid = create_user(db_session)
    fp.RESET_STORE.clear()
    fp.VERIFIED_SESSIONS.clear()
    token = "tok"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    fp.RESET_STORE[token_hash] = (uid, time.time() + 60)

    called = {}

    class DummyAdmin:
        def update_user_by_id(self, uid_arg, data):
            pass

        def sign_out_user(self, uid_arg, session_token=None):
            called["args"] = (uid_arg, session_token)

    class DummySB:
        def __init__(self):
            self.auth = type("A", (), {"admin": DummyAdmin()})()

    fp.get_supabase_client = lambda: DummySB()

    # simulate verifying with Authorization header
    req = type("Req", (), {"headers": {"Authorization": "Bearer sess"}})()
    fp.verify_reset_code(fp.CodePayload(code=token), req)
    fp.set_new_password(
        fp.PasswordPayload(code=token, new_password="StrongPass1234", confirm_password="StrongPass1234"),
        db_session,
    )

    assert called["args"] == (uid, "sess")


def test_reject_breached_password(db_session):
    uid = create_user(db_session)
    fp.RESET_STORE.clear()
    fp.VERIFIED_SESSIONS.clear()
    token = "breach"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    fp.RESET_STORE[token_hash] = (uid, time.time() + 60)
    fp.VERIFIED_SESSIONS[uid] = (token_hash, time.time() + 60, None)

    class DummyAdmin:
        def update_user_by_id(self, *_args, **_kwargs):
            raise AssertionError("should not call update")

        def sign_out_user(self, *_args, **_kwargs):
            raise AssertionError("should not call signout")

    class DummySB:
        def __init__(self):
            self.auth = type("A", (), {"admin": DummyAdmin()})()

    fp.get_supabase_client = lambda: DummySB()
    fp.is_pwned_password = lambda _pw: True

    with pytest.raises(HTTPException) as exc:
        fp.set_new_password(
            fp.PasswordPayload(
                code=token,
                new_password="StrongPass1234",
                confirm_password="StrongPass1234",
            ),
            db_session,
        )
    assert exc.value.status_code == 400
