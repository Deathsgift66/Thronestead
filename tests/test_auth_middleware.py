import asyncio
import os

from jose import jwt
from fastapi import Request
from starlette.responses import Response

from backend.auth_middleware import UserStateMiddleware
import backend.auth_middleware as am


def make_request(token=None):
    headers = []
    if token:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    return Request({"type": "http", "method": "GET", "headers": headers})


async def dummy_call(_):
    return Response("ok")


def test_middleware_accepts_token_with_audience(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    token = jwt.encode({"sub": "u1", "aud": "site"}, "secret", algorithm="HS256")
    middleware = UserStateMiddleware(None)
    req = make_request(token)
    resp = asyncio.run(middleware.dispatch(req, dummy_call))
    assert resp.body == b"ok"
    assert req.state.user.id == "u1"

def test_middleware_blocks_banned(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")
    token = jwt.encode({"sub": "u2"}, "secret", algorithm="HS256")
    middleware = UserStateMiddleware(None)
    req = make_request(token)

    class DummyDB:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        def execute(self, *args, **kwargs):
            return type("R", (), {"scalar": lambda self: True})()

    monkeypatch.setattr(am, "SessionLocal", lambda: DummyDB())
    monkeypatch.setattr(am, "has_active_ban", lambda db, **k: True)

    resp = asyncio.run(middleware.dispatch(req, dummy_call))
    assert resp.status_code == 403
