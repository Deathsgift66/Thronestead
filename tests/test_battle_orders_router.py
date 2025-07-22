from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.database import Base
from backend.models import Kingdom, User, WarsTactical, UnitMovement
from backend.routers.battle import OrdersPayload, issue_orders


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_data(db):
    db.add_all(
        [
            User(user_id="u1", username="A", email="a@test.com", kingdom_id=1),
            User(user_id="u2", username="B", email="b@test.com", kingdom_id=2),
            Kingdom(kingdom_id=1, user_id="u1", kingdom_name="K1"),
            Kingdom(kingdom_id=2, user_id="u2", kingdom_name="K2"),
            WarsTactical(war_id=1, attacker_kingdom_id=1, defender_kingdom_id=2),
            UnitMovement(
                movement_id=1,
                war_id=1,
                kingdom_id=1,
                unit_type="infantry",
                quantity=10,
                position_x=0,
                position_y=0,
            ),
        ]
    )
    db.commit()


def test_issue_orders_updates_unit():
    Session = setup_db()
    db = Session()
    seed_data(db)

    issue_orders(OrdersPayload(war_id=1, unit_id=1, x=3, y=4), user_id="u1", db=db)
    unit = db.query(UnitMovement).get(1)
    assert unit.target_tile_x == 3
    assert unit.target_tile_y == 4
    assert str(unit.issued_by) == "u1"


def test_issue_orders_forbidden():
    Session = setup_db()
    db = Session()
    seed_data(db)
    try:
        issue_orders(OrdersPayload(war_id=1, unit_id=1, x=1, y=1), user_id="u2", db=db)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        assert False
