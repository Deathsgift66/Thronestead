import asyncio
from fastapi import Request
from backend.routers.signup_check import check_signup_availability, SignupCheckRequest


def make_request():
    return Request({"type": "http", "method": "POST", "path": "/", "client": ("test", 0), "headers": []})


def test_check_available_empty_db(db_session):
    payload = SignupCheckRequest(username="newuser", display_name="NewUser", email="new@example.com")
    res = asyncio.run(check_signup_availability(payload, make_request(), db=db_session))
    assert res["username_available"] is True
    assert res["email_available"] is True
