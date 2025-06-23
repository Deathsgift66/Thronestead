# Project Name: Thronestead©
# File Name: test_notifications_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import uuid
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Notification, User
from backend.routers.notifications import (
    NotificationAction,
    cleanup_expired,
    clear_all,
    delete_notification,
    latest_notifications,
    list_notifications,
    mark_all_read,
    mark_read,
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
    sys_id = create_notification(db, None)

    res = list_notifications(user_id=uid, db=db)
    ids = [n["notification_id"] for n in res["notifications"]]
    assert nid in ids and sys_id in ids

    mark_read(NotificationAction(notification_id=nid), uid, db)
    notif = db.query(Notification).get(nid)
    assert notif.is_read
    assert notif.last_updated is not None

    latest = latest_notifications(user_id=uid, db=db)
    assert latest["notifications"][0]["notification_id"] in ids

    delete_notification(sys_id, uid, db)
    assert db.query(Notification).get(sys_id) is None

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
