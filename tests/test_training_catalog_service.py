# Project Name: Kingmakers Rise©
# File Name: test_training_catalog_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from services.training_catalog_service import list_units

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

def test_list_units_returns_rows():
    db = DummyDB()
    db.rows = [
        type('Row', (), {'_mapping': {'unit_id': 1, 'unit_name': 'Militia'}})()
    ]
    rows = list_units(db)
    assert rows[0]['unit_name'] == 'Militia'
    assert 'FROM training_catalog' in db.executed[0]
