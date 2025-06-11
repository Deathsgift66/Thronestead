import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Notification, User
from backend.routers.notifications import (
    NotificationAction,
    list_notifications,
    mark_read,
    mark_all_read,
    clear_all,
    cleanup_expired,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db):
    uid = uuid.uuid4()
    user = User(
        user_id=uid,
        username="test",
        display_name="test",
        email="t@example.com",
    )
    db.add(user)
    db.commit()
    return str(uid)


def create_notification(db, user_id, expires=None):
    notif = Notification(
        user_id=user_id,
        title="Test",
        message="msg",
        category="system",
        priority="normal",
        link_action="/",
        expires_at=expires,
        source_system="test",
    )
    db.add(notif)
    db.commit()
    return notif.notification_id


def test_notifications_flow():
    Session = setup_db()
    db = Session()
    uid = create_user(db)

    expired_date = datetime.utcnow() - timedelta(days=1)
    create_notification(db, uid, expires=expired_date)
    nid = create_notification(db, uid)

    res = list_notifications(uid, db)
    assert len(res["notifications"]) == 1
    assert res["notifications"][0]["notification_id"] == nid

    mark_read(NotificationAction(notification_id=nid), uid, db)
    notif = db.query(Notification).get(nid)
    assert notif.is_read
    assert notif.last_updated is not None

    nid2 = create_notification(db, uid)
    mark_all_read(uid, db)
    notif2 = db.query(Notification).get(nid2)
    assert notif2.is_read

    count_before = db.query(Notification).count()
    cleanup_expired(db)
    count_after = db.query(Notification).count()
    assert count_after < count_before

    clear_all(uid, db)
    assert db.query(Notification).filter(Notification.user_id == uid).count() == 0
