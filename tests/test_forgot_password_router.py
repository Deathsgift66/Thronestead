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
    fp.RATE_LIMIT.clear()
    fp.USER_RATE_LIMIT.clear()
    token = "TESTTOKEN1234"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    fp.RESET_STORE[token_hash] = (uid, time.time() + 60)
    fp.verify_reset_code(fp.CodePayload(code=token))
    assert uid in fp.VERIFIED_SESSIONS

    class DummyClient:
        class Auth:
            class Admin:
                def update_user_by_id(self, *_args, **_kwargs):
                    pass

            admin = Admin()

        auth = Auth()

    fp.get_supabase_client = lambda: DummyClient()
    req = DummyRequest()
    fp.set_new_password(
        fp.PasswordPayload(
            code=token,
            new_password="StrongPass1234",
            confirm_password="StrongPass1234",
        ),
        req,
        db_session,
    )
    assert uid not in fp.VERIFIED_SESSIONS
    assert token_hash not in fp.RESET_STORE
    notif = db_session.query(Notification).filter(Notification.user_id == uid).first()
    assert notif is not None


def test_reset_rate_limit_enforced(db_session):
    uid = create_user(db_session)
    fp.RATE_LIMIT.clear()
    fp.USER_RATE_LIMIT.clear()
    fp.RESET_STORE.clear()
    fp.VERIFIED_SESSIONS.clear()
    fp.RATE_LIMIT_MAX = 100
    fp.USER_RATE_LIMIT_MAX = 2

    class DummyClient:
        class Auth:
            class Admin:
                def update_user_by_id(self, *_args, **_kwargs):
                    pass

            admin = Admin()

        auth = Auth()

    fp.get_supabase_client = lambda: DummyClient()
    req = DummyRequest()
    token = "TOKEN"
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    payload = fp.PasswordPayload(
        code=token,
        new_password="StrongPass1234",
        confirm_password="StrongPass1234",
    )

    for _ in range(2):
        fp.RESET_STORE[token_hash] = (uid, time.time() + 60)
        fp.VERIFIED_SESSIONS[uid] = (token_hash, time.time() + 60)
        fp.set_new_password(payload, req, db_session)

    fp.RESET_STORE[token_hash] = (uid, time.time() + 60)
    fp.VERIFIED_SESSIONS[uid] = (token_hash, time.time() + 60)
    with pytest.raises(HTTPException) as exc:
        fp.set_new_password(payload, req, db_session)
    assert exc.value.status_code == 429
