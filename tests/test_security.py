import pytest
from jose import jwt
from fastapi import HTTPException
from sqlalchemy import text

from backend.security import require_active_user_id


def setup_user(db, uid, banned=False):
    db.execute(
        text(
            "INSERT INTO users (user_id, username, email, kingdom_name, is_banned) "
            "VALUES (:uid, 'u', 'e@example.com', 'k', :b)"
        ),
        {"uid": uid, "b": banned},
    )
    db.commit()


def token_for(uid, secret):
    return jwt.encode({"sub": uid}, secret, algorithm="HS256")


def test_require_active_user_allows_unbanned(db_session, monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    setup_user(db_session, "u1", False)
    token = token_for("u1", "secret")
    uid = require_active_user_id(
        authorization=f"Bearer {token}", x_user_id="u1", db=db_session
    )
    assert uid == "u1"


def test_require_active_user_blocks_banned(db_session, monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    setup_user(db_session, "u2", True)
    token = token_for("u2", "secret")
    with pytest.raises(HTTPException) as exc:
        require_active_user_id(
            authorization=f"Bearer {token}", x_user_id="u2", db=db_session
        )
    assert exc.value.status_code == 403


def test_require_active_user_allows_token_with_aud(db_session, monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    setup_user(db_session, "u3", False)
    token = jwt.encode({"sub": "u3", "aud": "authenticated"}, "secret", algorithm="HS256")
    uid = require_active_user_id(
        authorization=f"Bearer {token}", x_user_id="u3", db=db_session
    )
    assert uid == "u3"


class DummyReq:
    def __init__(self, ip=None, device_hash=None):
        self.headers = {}
        if ip:
            self.headers["x-forwarded-for"] = ip
        if device_hash:
            self.headers["X-Device-Hash"] = device_hash
        self.client = type("c", (), {"host": ip})


def test_ip_ban_blocks_request(db_session, monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    setup_user(db_session, "u4", False)
    db_session.execute(
        text(
            "INSERT INTO bans (ban_id, ip_address, ban_type, issued_by, is_active) "
            "VALUES ('b1', '1.1.1.1', 'ip', 'a1', true)"
        )
    )
    db_session.commit()
    token = token_for("u4", "secret")
    req = DummyReq(ip="1.1.1.1")
    with pytest.raises(HTTPException):
        require_active_user_id(
            request=req,
            authorization=f"Bearer {token}",
            x_user_id="u4",
            db=db_session,
        )


def test_device_ban_blocks_request(db_session, monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    setup_user(db_session, "u5", False)
    db_session.execute(
        text(
            "INSERT INTO bans (ban_id, device_hash, ban_type, issued_by, is_active) "
            "VALUES ('b2', 'abc', 'device', 'a1', true)"
        )
    )
    db_session.commit()
    token = token_for("u5", "secret")
    req = DummyReq(ip="2.2.2.2", device_hash="abc")
    with pytest.raises(HTTPException):
        require_active_user_id(
            request=req,
            authorization=f"Bearer {token}",
            x_user_id="u5",
            db=db_session,
        )
