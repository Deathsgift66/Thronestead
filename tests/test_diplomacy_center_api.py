from backend.routers import diplomacy_center as dc


class DummyResult:
    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def scalar(self):
        return self._scalar

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class DummyDB:
    def __init__(self):
        self.queries = []
        self.commits = 0

    def execute(self, query, params=None):
        q = str(query)
        self.queries.append(q)
        if "diplomacy_score" in q:
            return DummyResult(scalar=5)
        if "COUNT(*) FROM alliance_treaties" in q and "status = 'active'" in q:
            return DummyResult(scalar=2)
        if "COUNT(*) FROM alliance_wars" in q:
            return DummyResult(scalar=1)
        if "FROM alliance_treaties" in q and "JOIN" in q:
            return DummyResult(rows=[(1, "NAP", 2, "active", None, "Partner")])
        if "SELECT alliance_id" in q:
            return DummyResult(rows=[(1, 2, "NAP", "proposed", None)])
        return DummyResult()

    def commit(self):
        self.commits += 1


def test_metrics_returns_counts():
    db = DummyDB()
    res = dc.metrics(1, db=db)
    assert res["diplomacy_score"] == 5
    assert res["active_treaties"] == 2
    assert res["ongoing_wars"] == 1


def test_treaties_returns_list():
    db = DummyDB()
    rows = dc.treaties(1, db=db)
    assert rows[0]["partner_name"] == "Partner"


def test_propose_inserts():
    db = DummyDB()
    payload = dc.TreatyProposal(proposer_id=1, partner_alliance_id=2, treaty_type="NAP")
    dc.propose_treaty_api(payload, db=db)
    assert any("INSERT INTO alliance_treaties" in q for q in db.queries)
    assert db.commits == 1


def test_respond_updates():
    class RespDB(DummyDB):
        def execute(self, query, params=None):
            q = str(query)
            self.queries.append(q)
            if "SELECT alliance_id" in q:
                return DummyResult(rows=[(1, 2)])
            return super().execute(query, params)

    db = RespDB()
    payload = dc.TreatyResponse(treaty_id=5, response="accept")
    dc.respond_treaty_api(payload, db=db)
    assert any("UPDATE alliance_treaties" in q for q in db.queries)
    assert db.commits == 1
