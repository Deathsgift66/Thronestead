from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Kingdom, User
from backend.routers.progression_router import KnightPayload, promote_knight
from models.progression import KingdomKnight


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_promote_knight_updates_rank():
    Session = setup_db()
    db = Session()

    db.add_all([
        User(user_id="u1", username="Player", email="p@example.com", kingdom_id=1),
        Kingdom(kingdom_id=1, user_id="u1", kingdom_name="Test"),
        KingdomKnight(kingdom_id=1, knight_name="Lancelot", rank="Squire"),
    ])
    db.commit()

    res = promote_knight(KnightPayload(knight_name="Lancelot"), user_id="u1", db=db)
    knight = db.query(KingdomKnight).filter_by(knight_name="Lancelot").first()

    assert knight.rank == "Knight"
    assert res["new_rank"] == "Knight"
