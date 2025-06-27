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
