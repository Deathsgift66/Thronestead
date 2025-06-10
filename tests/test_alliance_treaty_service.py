from services.alliance_treaty_service import (
    propose_treaty,
    accept_treaty,
    cancel_treaty,
    list_active_treaties,
    list_incoming_proposals,
    list_outgoing_proposals,
)


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.row = None
        self.rows = []
        self.commits = 0

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append((q, params))
        if "SELECT 1 FROM alliance_treaties" in q:
            return DummyResult(row=self.row)
        if q.startswith("SELECT treaty_id"):
            return DummyResult(rows=self.rows)
        return DummyResult()

    def commit(self):
        self.commits += 1


def test_propose_treaty_inserts():
    db = DummyDB()
    propose_treaty(db, 1, 2, "NAP")
    assert any("INSERT INTO alliance_treaties" in q for q, _ in db.queries)
    assert db.commits == 1


def test_propose_existing_raises():
    db = DummyDB()
    db.row = (1,)
    try:
        propose_treaty(db, 1, 2, "NAP")
    except ValueError:
        assert True
    else:
        assert False


def test_accept_and_cancel():
    db = DummyDB()
    accept_treaty(db, 5)
    cancel_treaty(db, 5)
    q = " ".join(q for q, _ in db.queries)
    assert "UPDATE alliance_treaties SET status = 'active'" in q
    assert "UPDATE alliance_treaties SET status = 'cancelled'" in q
    assert db.commits == 2


def test_list_functions():
    db = DummyDB()
    db.rows = [(1, 1, "Pact", 2, "active", "2025-01-01")]
    active = list_active_treaties(db, 1)
    incoming = list_incoming_proposals(db, 1)
    outgoing = list_outgoing_proposals(db, 1)
    assert active[0]["treaty_id"] == 1
    assert incoming[0]["treaty_id"] == 1
    assert outgoing[0]["treaty_id"] == 1
