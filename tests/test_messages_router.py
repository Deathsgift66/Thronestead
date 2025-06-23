# Project Name: Thronestead©
# File Name: test_messages_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import PlayerMessage, User
from backend.routers import messages
from backend.routers.messages import (
    DeletePayload,
    MessagePayload,
    delete_message,
    get_message,
    send_message,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db, username="u1"):
    uid = str(uuid.uuid4())
    user = User(
        user_id=uid, username=username, display_name=username, email=f"{username}@e.com"
    )
    db.add(user)
    db.commit()
    return uid


def test_full_message_flow():
    Session = setup_db()
    db = Session()
    sender = create_user(db, "sender")
    recipient = create_user(db, "rec")

    send_message(
        MessagePayload(
            recipient="rec", content="Hello", subject="Hi", category="player"
        ),
        user_id=sender,
    )
    res = messages.list_inbox(user_id=recipient, db=db)
    assert len(res["messages"]) == 1
    mid = res["messages"][0]["message_id"]

    res_msg = get_message(mid, user_id=recipient)
    assert res_msg["subject"] == "Hi"
    assert res_msg["category"] == "player"

    msg = db.query(PlayerMessage).get(mid)
    assert msg.is_read

    delete_message(DeletePayload(message_id=mid), user_id=recipient)


def seed_users(db):
    u1 = User(user_id="u1", username="Arthur", email="a@example.com")
    u2 = User(user_id="u2", username="Lancelot", email="l@example.com")
    db.add_all([u1, u2])
    db.commit()
    return u1.user_id, u2.user_id


def test_list_inbox_returns_messages():
    Session = setup_db()
    db = Session()
    uid1, uid2 = seed_users(db)
    msg = PlayerMessage(user_id=uid2, recipient_id=uid1, message="Hail")
    db.add(msg)
    db.commit()
    db.execute(
        text(
            "INSERT INTO message_metadata (message_id, key, value) VALUES (:mid, 'subject', 'Greetings')"
        ),
        {"mid": msg.message_id},
    )
    db.commit()

    res = messages.list_inbox(user_id=uid1, db=db)
    assert len(res["messages"]) == 1
    assert res["messages"][0]["sender"] == "Lancelot"
    assert res["messages"][0]["subject"] == "Greetings"


def test_view_message_marks_read():
    Session = setup_db()
    db = Session()
    uid1, uid2 = seed_users(db)
    msg = PlayerMessage(user_id=uid2, recipient_id=uid1, message="Hail")
    db.add(msg)
    db.commit()
    db.execute(
        text(
            "INSERT INTO message_metadata (message_id, key, value) VALUES (:mid, 'subject', 'Hey')"
        ),
        {"mid": msg.message_id},
    )
    db.commit()

    res = messages.view_message(message_id=msg.message_id, user_id=uid1)
    assert res["is_read"] is True
    assert res["sender"] == "Lancelot"
    assert res["subject"] == "Hey"


def test_delete_message_sets_flag():
    Session = setup_db()
    db = Session()
    uid1, uid2 = seed_users(db)
    msg = PlayerMessage(user_id=uid2, recipient_id=uid1, message="Hail")
    db.add(msg)
    db.commit()

    messages.delete_message(message_id=msg.message_id, user_id=uid1)
    row = db.query(PlayerMessage).filter_by(message_id=msg.message_id).first()
    assert row is None


def test_mark_all_read_updates_rows():
    Session = setup_db()
    db = Session()
    uid1, uid2 = seed_users(db)
    db.add(PlayerMessage(user_id=uid2, recipient_id=uid1, message="Hail"))
    db.add(PlayerMessage(user_id=uid2, recipient_id=uid1, message="Yo"))
    db.commit()

    messages.mark_all_read(user_id=uid1)
    rows = db.query(PlayerMessage).filter_by(recipient_id=uid1).all()
    assert all(r.is_read for r in rows)
