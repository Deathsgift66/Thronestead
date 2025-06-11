from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import uuid

from backend.db_base import Base
from backend.models import User, PlayerMessage
from backend.routers.messages import (
    send_message,
    list_messages,
    get_message,
    delete_message,
    MessagePayload,
    DeletePayload,
)


from backend.db_base import Base
from backend.models import User, PlayerMessage
from backend.routers import messages

def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db, username="u1"):
    uid = str(uuid.uuid4())
    user = User(user_id=uid, username=username, display_name=username, email=f"{username}@e.com")
    db.add(user)
    db.commit()
    return uid

def test_full_message_flow():
    Session = setup_db()
    db = Session()
    sender = create_user(db, "sender")
    recipient = create_user(db, "rec")

    send_message(MessagePayload(recipient="rec", subject="Hi", content="Hello"), user_id=sender, db=db)
    res = list_messages(user_id=recipient, db=db)
    assert len(res["messages"]) == 1
    mid = res["messages"][0]["message_id"]

    detail = get_message(mid, user_id=recipient, db=db)
    assert detail["subject"] == "Hi"

    msg = db.query(PlayerMessage).get(mid)
    assert msg.is_read

    delete_message(DeletePayload(message_id=mid), user_id=recipient, db=db)
    assert msg.deleted_by_recipient

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
    db.add(PlayerMessage(user_id=uid2, recipient_id=uid1, message="Hail"))
    db.commit()

    res = messages.list_inbox(user_id=uid1, db=db)
    assert len(res["messages"]) == 1
    assert res["messages"][0]["sender"] == "Lancelot"


def test_view_message_marks_read():
    Session = setup_db()
    db = Session()
    uid1, uid2 = seed_users(db)
    msg = PlayerMessage(user_id=uid2, recipient_id=uid1, message="Hail")
    db.add(msg)
    db.commit()

    res = messages.view_message(message_id=msg.message_id, user_id=uid1, db=db)
    assert res["is_read"] is True
    assert res["sender"] == "Lancelot"


def test_delete_message_sets_flag():
    Session = setup_db()
    db = Session()
    uid1, uid2 = seed_users(db)
    msg = PlayerMessage(user_id=uid2, recipient_id=uid1, message="Hail")
    db.add(msg)
    db.commit()

    messages.delete_message(message_id=msg.message_id, user_id=uid1, db=db)
    row = db.query(PlayerMessage).filter_by(message_id=msg.message_id).first()
    assert row.deleted_by_recipient is True

