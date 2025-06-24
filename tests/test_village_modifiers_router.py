# Project Name: Thronestead©
# File Name: test_village_modifiers_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import uuid
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User, VillageModifier
from backend.routers.village_modifiers import (
    ModifierPayload,
    apply_modifier,
    cleanup_expired,
    list_modifiers,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db):
    uid = uuid.uuid4()
    user = User(user_id=uid, username="test", email="t@example.com")
    db.add(user)
    db.commit()
    return str(uid)


def test_modifier_flow():
    Session = setup_db()
    db = Session()
    uid = create_user(db)

    payload = ModifierPayload(
        village_id=1,
        resource_bonus={"wood": 10},
        troop_bonus={"defense": 5},
        source="quest",
        applied_by=uid,
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    apply_modifier(payload, db)

    res = list_modifiers(1, db)
    assert len(res["modifiers"]) == 1
    assert res["modifiers"][0]["resource_bonus"]["wood"] == 10

    # expire and cleanup
    db.query(VillageModifier).update(
        {VillageModifier.expires_at: datetime.utcnow() - timedelta(days=1)}
    )
    db.commit()
    cleanup_expired(db)
    res2 = list_modifiers(1, db)
    assert len(res2["modifiers"]) == 0


def test_multiple_modifiers_coexist():
    Session = setup_db()
    db = Session()
    uid = create_user(db)

    apply_modifier(
        ModifierPayload(
            village_id=1,
            resource_bonus={"wood": 5},
            source="quest",
            applied_by=uid,
            expires_at=None,
        ),
        db,
    )

    apply_modifier(
        ModifierPayload(
            village_id=1,
            troop_bonus={"attack": 3},
            source="building",
            applied_by=uid,
            expires_at=None,
        ),
        db,
    )

    res = list_modifiers(1, db)
    sources = {m["source"] for m in res["modifiers"]}
    assert sources == {"quest", "building"}
