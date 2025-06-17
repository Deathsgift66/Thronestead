from fastapi import HTTPException
from backend.routers import kingdom


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.profile_row = None
        self.religion_row = None
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        q = str(query).lower().strip()
        self.queries.append((q, params))
        if "from kingdoms" in q and "user_id" in q:
            return DummyResult(self.profile_row)
        if "from kingdom_religion" in q:
            return DummyResult(self.religion_row)
        return DummyResult()

    def commit(self):
        self.committed = True


def test_kingdom_profile_returns_data():
    db = DummyDB()
    db.profile_row = (
        1,
        "Ruler",
        "Title",
        "Realm",
        "M",
        "Desc",
        "west",
        "b.png",
        "e.png",
        False,
    )
    db.religion_row = ("Light",)

    result = kingdom.kingdom_profile(user_id="u1", db=db)
    assert result["kingdom_name"] == "Realm"
    assert result["religion"] == "Light"


def test_kingdom_profile_not_found():
    db = DummyDB()
    db.profile_row = None
    try:
        kingdom.kingdom_profile(user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False


def test_update_kingdom_profile_runs_update():
    db = DummyDB()
    db.profile_row = (1,)
    payload = kingdom.KingdomUpdatePayload(kingdom_name="New")
    kingdom.update_kingdom_profile(payload, user_id="u1", db=db)
    joined = " ".join(db.queries[-2][0].split())
    assert "update kingdoms" in joined
    assert db.committed


def test_update_kingdom_profile_not_found():
    db = DummyDB()
    db.profile_row = None
    try:
        kingdom.update_kingdom_profile(kingdom.KingdomUpdatePayload(), user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False
