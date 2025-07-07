from services.name_service import name_in_use
from backend.models import User, Kingdom


def test_name_in_use_detects_existing(db_session):
    db_session.add(User(user_id="u1", username="Hero", display_name="Hero", kingdom_name="Realm", email="h@e.com"))
    db_session.add(Kingdom(kingdom_id=1, user_id="u1", kingdom_name="Realm", ruler_name="King"))
    db_session.commit()

    assert name_in_use(db_session, "hero")
    assert name_in_use(db_session, "realm")
    assert name_in_use(db_session, " king ")
    assert not name_in_use(db_session, "unique")


def test_name_in_use_empty_and_no_rows(db_session):
    # No users or kingdoms added
    assert not name_in_use(db_session, "")
    assert not name_in_use(db_session, None)
    assert not name_in_use(db_session, "unknown")
