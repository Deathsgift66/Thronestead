import pytest
from fastapi import HTTPException

from backend.routers import titles_router as tr

class DummyDB:
    pass


def test_award_title_forbidden(monkeypatch):
    monkeypatch.setattr(tr, "award_title", lambda db, kid, title: None)
    monkeypatch.setattr(tr, "get_kingdom_id", lambda db, uid: 1)

    def deny(uid, db):
        raise HTTPException(status_code=403)

    monkeypatch.setattr(tr, "verify_admin", deny)

    payload = tr.TitlePayload(title="Hero")
    with pytest.raises(HTTPException) as exc:
        tr.award_title_endpoint(payload, user_id="u1", db=DummyDB())
    assert exc.value.status_code == 403

def test_award_title_admin(monkeypatch):
    called = {}
    monkeypatch.setattr(tr, "get_kingdom_id", lambda db, uid: 5)
    def fake_award(db, kid, title):
        called["kid"] = kid
        called["title"] = title
    monkeypatch.setattr(tr, "award_title", fake_award)
    monkeypatch.setattr(tr, "verify_admin", lambda uid, db: None)

    payload = tr.TitlePayload(title="Champion")
    result = tr.award_title_endpoint(payload, user_id="admin", db=DummyDB())
    assert result["message"] == "Title awarded"
    assert called["kid"] == 5
    assert called["title"] == "Champion"

