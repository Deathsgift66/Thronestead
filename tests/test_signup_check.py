import asyncio
import pytest
from fastapi import Request, HTTPException
from sqlalchemy import text
from backend.routers.signup_check import check_signup_availability, SignupCheckRequest


def make_request():
    return Request({"type": "http", "method": "POST", "path": "/", "client": ("test", 0), "headers": []})


def test_check_available_empty_db(db_session):
    payload = SignupCheckRequest(username="newuser", display_name="NewUser", email="new@example.com")
    res = asyncio.run(check_signup_availability(payload, make_request(), db=db_session))
    assert res["username_available"] is True
    assert res["email_available"] is True
    assert res["display_available"] is True


def test_check_unavailable_when_taken(db_session):
    db_session.execute(
        text(
            "INSERT INTO users (user_id, username, display_name, kingdom_name, email) "
            "VALUES ('u1', 'taken', 'Display', 'Realm', 'used@example.com')"
        )
    )
    db_session.commit()
    payload = SignupCheckRequest(
        username="taken",
        display_name="Display",
        email="used@example.com",
    )
    res = asyncio.run(check_signup_availability(payload, make_request(), db=db_session))
    assert res["username_available"] is False
    assert res["email_available"] is False
    assert res["display_available"] is False


def test_check_missing_fields(db_session):
    payload = SignupCheckRequest()
    with pytest.raises(HTTPException):
        asyncio.run(check_signup_availability(payload, make_request(), db=db_session))
