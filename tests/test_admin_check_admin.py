from backend.routers import admin as admin_router

class DummyResult:
    def __init__(self, row=(True,)):
        self._row = row
    def scalar(self):
        return self._row[0]
    def fetchone(self):
        return self._row

class DummyDB:
    def __init__(self):
        self.queries = []
    def execute(self, query, params=None):
        q = str(query).lower()
        self.queries.append((q, params))
        if q.strip().startswith("select is_admin"):
            return DummyResult()
        if q.strip().startswith("insert into audit_log"):
            return DummyResult()
        return DummyResult()
    def commit(self):
        pass


def test_check_admin_verifies():
    db = DummyDB()
    res = admin_router.check_admin(admin_user_id="a1", db=db)
    assert res["is_admin"] is True
    assert any("select is_admin" in q[0] for q in db.queries)


def test_log_view_event_inserts():
    db = DummyDB()
    res = admin_router.log_view_event(admin_user_id="a1", db=db)
    assert res["status"] == "logged"
    assert any("insert into audit_log" in q[0] for q in db.queries)

