import uuid
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User
from backend.routers import reauth
from backend.security import validate_reauth_token


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    engine.execute(
        text(
            "CREATE TABLE reauth_tokens (token TEXT PRIMARY KEY, user_id TEXT, expires_at TIMESTAMP)"
        )
    )
    engine.execute(
        text(
            "CREATE TABLE audit_log (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, details TEXT, created_at TEXT)"
        )
    )
    return Session


def create_user(db):
    uid = str(uuid.uuid4())
    user = User(user_id=uid, username="t", display_name="t", email="e@example.com", kingdom_name="k")
    db.add(user)
    db.commit()
    return uid


class DummyAuth:
    def __init__(self, mode="ok"):
        self.mode = mode

    def sign_in_with_password(self, *_args, **_kwargs):
        if self.mode == "error":
            return {"error": "bad"}
        if self.mode == "fail":
            raise Exception("fail")
        return {"session": "s"}

    def verify_otp(self, *_args, **_kwargs):
        if self.mode == "2fa_fail":
            return {"error": "bad"}
        return {}


class DummyClient:
    def __init__(self, mode="ok"):
        self.auth = DummyAuth(mode)


def test_reauth_success_creates_token_and_logs(monkeypatch):
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient())
    captured = {}

    def fake_log_action(_db, user_id, action, _details):
        captured["uid"] = user_id
        captured["action"] = action

    monkeypatch.setattr(reauth, "log_action", fake_log_action)
    payload = reauth.ReauthPayload(password="p")
    res = reauth.reauthenticate(payload, user_id=uid, db=db)
    row = db.execute(text("SELECT token FROM reauth_tokens WHERE user_id=:u"), {"u": uid}).fetchone()
    assert row is not None
    assert res["token"] == row[0]
    assert captured["action"] == "reauth_success"
    assert validate_reauth_token(db, uid, res["token"]) is True


def test_reauth_failure_logs(monkeypatch):
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummyClient("error"))
    captured = {}

    def fake_log_action(_db, user_id, action, _details):
        captured["uid"] = user_id
        captured["action"] = action

    monkeypatch.setattr(reauth, "log_action", fake_log_action)
    payload = reauth.ReauthPayload(password="bad")
    try:
        reauth.reauthenticate(payload, user_id=uid, db=db)
    except Exception:
        pass
    assert captured["action"] == "reauth_fail"


def test_validate_reauth_token_expired():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.execute(
        text(
            "INSERT INTO reauth_tokens (token, user_id, expires_at) VALUES (:t,:u,:e)"
        ),
        {"t": "tok", "u": uid, "e": datetime.utcnow() - timedelta(seconds=1)},
    )
    db.commit()
    assert validate_reauth_token(db, uid, "tok") is False
