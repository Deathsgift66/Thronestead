import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User, Alliance, PlayerMessage, AllianceNotice, War
from backend.routers.compose import (
    send_message,
    create_notice,
    propose_treaty,
    declare_war,
    MessagePayload,
    NoticePayload,
    TreatyPayload,
    WarPayload,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    engine.execute(
        text(
            """
            CREATE TABLE alliance_treaties (
                treaty_id INTEGER PRIMARY KEY AUTOINCREMENT,
                alliance_id INTEGER,
                treaty_type TEXT,
                partner_alliance_id INTEGER,
                status TEXT
            )
            """
        )
    )
    return Session


def create_user(db, uid, alliance_id=None):
    db.add(User(user_id=uid, username=f"u{uid}", display_name="U", email=f"{uid}@t.test", kingdom_name="K", alliance_id=alliance_id))
    if alliance_id:
        db.add(Alliance(alliance_id=alliance_id, name=f"A{alliance_id}"))
    db.commit()


def test_send_message_inserts_record():
    Session = setup_db()
    db = Session()
    u1 = str(uuid.uuid4())
    u2 = str(uuid.uuid4())
    create_user(db, u1)
    create_user(db, u2)
    res = send_message(MessagePayload(recipient_id=u2, message="hi"), u1, db)
    assert res["status"] == "sent"
    assert db.query(PlayerMessage).count() == 1


def test_create_notice_inserts_record():
    Session = setup_db()
    db = Session()
    uid = str(uuid.uuid4())
    create_user(db, uid, alliance_id=1)
    res = create_notice(NoticePayload(title="T", message="M", alliance_id=1), uid, db)
    assert res["status"] == "created"
    assert db.query(AllianceNotice).count() == 1


def test_propose_treaty_row_created():
    Session = setup_db()
    db = Session()
    uid = str(uuid.uuid4())
    create_user(db, uid, alliance_id=1)
    db.add(Alliance(alliance_id=2, name="B"))
    db.commit()
    res = propose_treaty(TreatyPayload(partner_alliance_id=2, treaty_type="trade_pact"), uid, db)
    row = db.execute(text("SELECT * FROM alliance_treaties")).fetchone()
    assert res["status"] == "proposed" and row is not None


def test_declare_war_creates_record():
    Session = setup_db()
    db = Session()
    u1 = str(uuid.uuid4())
    u2 = str(uuid.uuid4())
    create_user(db, u1)
    create_user(db, u2)
    res = declare_war(WarPayload(defender_id=u2, war_reason="R"), u1, db)
    war = db.query(War).first()
    assert res["status"] == "pending" and war
