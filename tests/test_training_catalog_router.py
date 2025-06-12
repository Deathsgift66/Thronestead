from backend.routers.training_catalog import get_catalog

class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []
    def fetchall(self):
        return self._rows

class DummyDB:
    def __init__(self):
        self.executed = []
        self.rows = []
    def execute(self, query, params=None):
        self.executed.append(str(query))
        return DummyResult(self.rows)

def test_get_catalog_returns_rows():
    db = DummyDB()
    db.rows = [
        type('Row', (), {'_mapping': {'unit_id': 1, 'unit_name': 'Militia'}})()
    ]
    res = get_catalog(user_id='u1', db=db)
    assert res['catalog'][0]['unit_name'] == 'Militia'
    assert 'FROM training_catalog' in db.executed[0]
