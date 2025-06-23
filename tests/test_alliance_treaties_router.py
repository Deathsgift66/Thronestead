from backend.routers import alliance_treaties_router as router


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def mappings(self):
        return self

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.rows = []

    def execute(self, query, params=None):
        return DummyResult(rows=self.rows)


def test_get_treaty_types_returns_rows():
    db = DummyDB()
    db.rows = [{"treaty_type": "NAP", "display_name": "Non-Aggression Pact"}]
    result = router.get_treaty_types(db=db)
    assert result["types"][0]["treaty_type"] == "NAP"


def test_alt_propose_delegates(monkeypatch):
    """alt_propose_treaty should delegate to propose_treaty."""

    called = {}

    def dummy_propose(payload, user_id=None, db=None):
        called["payload"] = payload
        called["user_id"] = user_id
        called["db"] = db
        return {"status": "proposed"}

    monkeypatch.setattr(router, "propose_treaty", dummy_propose)
    payload = router.ProposePayload(treaty_type="NAP", partner_alliance_id=2)
    db = object()
    res = router.alt_propose_treaty(payload, user_id="u1", db=db)
    assert res["status"] == "proposed"
    assert called["payload"] == payload
    assert called["user_id"] == "u1"
    assert called["db"] is db
