import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import KingdomResources, KingdomVillage, VillageProduction
from services import production_tick_service


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_tick_kingdom_production_applies_bonus(monkeypatch):
    Session = setup_db()
    db = Session()
    db.add(KingdomResources(kingdom_id=1, wood=0, stone=0))
    db.add(KingdomVillage(village_id=1, kingdom_id=1, village_name="V1"))
    db.add(VillageProduction(village_id=1, resource_type="wood", production_rate=5))
    db.add(VillageProduction(village_id=1, resource_type="stone", production_rate=10))
    db.commit()

    def fake_mods(db_arg, kid, use_cache=True):
        return {"production_bonus": {"tech": 25}}

    monkeypatch.setattr(production_tick_service.progression_service, "get_total_modifiers", fake_mods)

    gained = production_tick_service.tick_kingdom_production(db, 1)
    assert gained == {"wood": 6, "stone": 12}

    row = db.query(KingdomResources).filter_by(kingdom_id=1).one()
    assert row.wood == 6 and row.stone == 12


def test_tick_returns_empty_without_villages(monkeypatch):
    Session = setup_db()
    db = Session()
    db.add(KingdomResources(kingdom_id=1))
    db.commit()

    monkeypatch.setattr(
        production_tick_service.progression_service,
        "get_total_modifiers",
        lambda *a, **k: {"production_bonus": {"tech": 50}},
    )

    gained = production_tick_service.tick_kingdom_production(db, 1)
    assert gained == {}
    row = db.query(KingdomResources).filter_by(kingdom_id=1).one()
    assert row.wood == 0
