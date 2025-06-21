import datetime
from backend.routers import spy as spy_router

class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []
    def fetchall(self):
        return [type('Row', (), {'_mapping': r}) for r in self._rows]

class DummyDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.queries = []
    def execute(self, q, params=None):
        self.queries.append((str(q), params))
        return DummyResult(self.rows)


def test_get_spy_log_returns_rows(monkeypatch):
    db = DummyDB(rows=[{
        'mission_type': 'scout',
        'target_id': 2,
        'target_name': 'Enemy',
        'outcome': 'success',
        'accuracy': 90,
        'detected': False,
        'spies_lost': 0,
        'timestamp': datetime.datetime(2025, 1, 1)
    }])

    monkeypatch.setattr(spy_router, 'get_kingdom_id', lambda d, uid: 1)
    result = spy_router.get_spy_log(user_id='u1', db=db)
    assert result['logs'][0]['mission_type'] == 'scout'
    assert db.queries[0][1]['kid'] == 1

