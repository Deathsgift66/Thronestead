from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import UserReport
from backend.routers.reports import ReportPayload, list_reports, submit_report


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_report_submission_and_listing():
    Session = setup_db()
    db = Session()
    uid = "u1"

    res = submit_report(
        ReportPayload(category="harassment", description="they insulted me"),
        user_id=uid,
        db=db,
    )
    assert res["status"] == "submitted"
    rid = res["report_id"]

    result = list_reports(user_id=uid, db=db)
    assert len(result["reports"]) == 1
    assert result["reports"][0]["report_id"] == rid
