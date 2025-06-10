from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import User, PlayerMessage
from backend.routers import messages


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


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
