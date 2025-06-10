import asyncio
from backend.routers.admin import get_admin_alerts

class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []
    def fetchall(self):
        return self._rows

class DummyDB:
    def __init__(self):
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append((str(query), params))
        return DummyResult()

def test_filters_included_in_query():
    db = DummyDB()
    asyncio.run(get_admin_alerts(start="2025-01-01", end="2025-01-02", admin_id="a1", db=db))
    joined = " ".join(db.queries[0][0].split()).lower()
    assert "created_at >= :start" in joined
    assert db.queries[0][1]["start"] == "2025-01-01"

