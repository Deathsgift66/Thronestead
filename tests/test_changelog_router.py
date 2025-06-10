import asyncio
from backend.routers import changelog

class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
    def select(self, *args):
        return self
    def order(self, *args, **kwargs):
        return self
    def limit(self, *args):
        return self
    def execute(self):
        return {'data': self._data}

class DummyClient:
    def __init__(self, tables):
        self.tables = tables
    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_returns_sorted_entries():
    entries = [
        {'version': '1.0.0', 'release_date': '2025-01-01', 'changes': ['init']},
        {'version': '1.1.0', 'release_date': '2025-02-01', 'changes': ['new']},
    ]
    client = DummyClient({'game_changelog': entries})
    changelog.get_supabase_client = lambda: client
    result = asyncio.run(changelog.get_changelog(user_id='u1'))
    assert result['entries'][0]['version'] == '1.1.0'
    assert len(result['entries']) == 2
