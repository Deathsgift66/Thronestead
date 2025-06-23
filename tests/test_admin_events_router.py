from backend.routers import admin_events


class DummyResult:
    def __init__(self, row=None):
        self._row = row or (1,)

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        lower = q.strip().lower()
        if lower.startswith("select is_admin"):
            return DummyResult((True,))
        if "insert into global_events" in lower:
            return DummyResult((1,))
        return DummyResult()

    def commit(self):
        pass


def test_create_event_inserts_and_logs():
    db = DummyDB()
    payload = admin_events.EventPayload(name="Test")
    res = admin_events.create_event(payload, admin_user_id="a1", db=db)
    assert res["status"] == "created"
    assert any("insert into global_events" in q[0].lower() for q in db.queries)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)
