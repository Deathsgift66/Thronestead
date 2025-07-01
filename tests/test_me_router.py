import asyncio

import pytest
from jose import jwt
from sqlalchemy import text

from fastapi import HTTPException
from backend.security import get_current_user
from backend.routers import me


def make_request(token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return type("Req", (), {"headers": headers})()


def create_user_row(db):
    db.execute(
        text(
            "INSERT INTO users (user_id, username, kingdom_id, alliance_id, setup_complete)"
            " VALUES ('u1', 'name', 1, 2, 1)"
        )
    )
    db.commit()


def test_get_current_user_success(db_session, monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    token = jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")
    create_user_row(db_session)
    req = make_request(token)
    user = asyncio.run(get_current_user(req, db=db_session))
    assert user["user_id"] == "u1"
    assert user["username"] == "name"
    assert user["kingdom_id"] == 1
    assert user["alliance_id"] == 2
    assert user["setup_complete"] is True


def test_get_current_user_missing(db_session):
    req = make_request()
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(req, db=db_session))


def test_get_current_user_invalid(db_session, monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    token = "invalid"
    req = make_request(token)
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(req, db=db_session))


def test_me_route_returns_user(monkeypatch):
    token = jwt.encode(
        {"sub": "u1", "email": "u@example.com", "role": "player"},
        "secret",
        algorithm="HS256",
    )
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    result = me.get_me(Authorization=f"Bearer {token}")
    assert result == {
        "user_id": "u1",
        "email": "u@example.com",
        "roles": "player",
    }


