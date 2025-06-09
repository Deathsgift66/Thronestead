from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Alliance, ProjectAllianceCatalogue, User
from backend.routers.alliance_projects import list_projects


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db):
    user = User(
        user_id='00000000-0000-0000-0000-000000000001',
        username='tester',
        display_name='Tester',
        email='t@example.com'
    )
    db.add(user)
    db.commit()
    return user.user_id


def test_list_projects_filters_by_level():
    Session = setup_db()
    db = Session()
    create_user(db)
    db.add(Alliance(alliance_id=1, name='A', level=2))
    db.add(ProjectAllianceCatalogue(project_code='p1', project_name='One', requires_alliance_level=1))
    db.add(ProjectAllianceCatalogue(project_code='p2', project_name='Two', requires_alliance_level=5))
    db.commit()

    res = list_projects(1, db)
    assert len(res["projects"]) == 1
    assert res["projects"][0]["project_code"] == 'p1'
