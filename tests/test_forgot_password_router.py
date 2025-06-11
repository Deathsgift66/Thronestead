import hashlib
import time
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User, Notification
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


def test_request_stores_token():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    fp.RESET_STORE.clear()
    req = DummyRequest()
    fp.request_password_reset(fp.EmailPayload(email="e@example.com"), req, db)
    assert len(fp.RESET_STORE) == 1
    stored_uid = next(iter(fp.RESET_STORE.values()))[0]
    assert stored_uid == uid


def test_full_reset_flow():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
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
        db,
    )
    assert uid not in fp.VERIFIED_SESSIONS
    assert token_hash not in fp.RESET_STORE
    notif = db.query(Notification).filter(Notification.user_id == uid).first()
    assert notif is not None
