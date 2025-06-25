import asyncio
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User
from backend.routers import auth
from backend.routers import forgot_password as fp


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    engine.execute(
        text(
            "CREATE TABLE audit_log (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, details TEXT, created_at TEXT)"
        )
    )
    return Session


def create_user(db):
    uid = str(uuid.uuid4())
    user = User(user_id=uid, username="t", display_name="t", email="e@example.com")
    db.add(user)
    db.commit()
    return uid


class DummyRequest:
    def __init__(self, host="1.1.1.1"):
        self.client = type("c", (), {"host": host})


def test_request_stores_token_via_auth():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    fp.RESET_STORE.clear()
    req = DummyRequest()
    auth.request_password_reset(auth.EmailPayload(email="e@example.com"), req, db)
    assert len(fp.RESET_STORE) == 1
    stored_uid = next(iter(fp.RESET_STORE.values()))[0]
    assert stored_uid == uid


def test_validate_session_via_auth(monkeypatch):
    class DummyAuth:
        def __init__(self, user):
            self._user = user
            self.called_token = None

        def get_user(self, token):
            self.called_token = token
            return self._user

    class DummySupabase:
        def __init__(self, user):
            self.auth = DummyAuth(user)

    dummy = DummySupabase({"id": "u1"})

    async def fake_validate(request):
        token = request.headers.get("Authorization").split()[1]
        return dummy.auth.get_user(token)

    monkeypatch.setattr(auth, "_validate_session", fake_validate)
    req = type("Req", (), {"headers": {"Authorization": "Bearer tok"}})()
    result = asyncio.run(auth.validate_session(req))
    assert result == {"id": "u1"}


def test_resend_confirmation_via_auth(monkeypatch):
    called = {}

    def dummy(payload):
        called["email"] = payload.email
        return {"status": "sent"}

    monkeypatch.setattr(auth, "_resend_confirmation", dummy)
    payload = auth.ResendPayload(email="e@example.com")
    res = auth.resend_confirmation(payload)
    assert res["status"] == "sent"
    assert called["email"] == "e@example.com"

