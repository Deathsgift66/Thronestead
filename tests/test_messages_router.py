from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from backend.database import Base
from backend.models import User, PlayerMessage
from backend.routers.messages import (
    send_message,
    list_messages,
    get_message,
    delete_message,
    MessagePayload,
    DeletePayload,
)

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

