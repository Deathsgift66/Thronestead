# Project Name: Thronestead©
# File Name: test_resources_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import KingdomResources, User
from backend.routers import resources
from backend.routers.resources import get_resources


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_data(db):
    user = User(
        user_id="u1",
        username="tester",
        display_name="Tester",
        email="t@example.com",
        kingdom_id=1,
    )
    db.add(user)
    db.add(KingdomResources(kingdom_id=1, wood=100, gold=50))
    db.commit()
    return user.user_id


def test_get_resources_returns_row():
    Session = setup_db()
    db = Session()
    uid = seed_data(db)

    res = get_resources(user_id=uid, db=db)
    assert res["resources"]["wood"] == 100
    assert res["resources"]["gold"] == 50


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self._single = False

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._single:
            return {"data": self._data[0] if self._data else None}
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_get_resources_uses_supabase():
    tables = {
        "kingdoms": [{"kingdom_id": 2}],
        "kingdom_resources": [
            {
                "kingdom_id": 2,
                "wood": 5,
                "gold": 7,
                "created_at": "2025-01-01",
                "last_updated": "2025-01-01",
            }
        ],
    }
    resources.get_supabase_client = lambda: DummyClient(tables)
    res = get_resources(user_id="u1", db=None)
    assert res["resources"]["wood"] == 5
    assert "kingdom_id" not in res["resources"]
