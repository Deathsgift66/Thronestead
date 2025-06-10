import asyncio
from backend.routers import login_routes

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
        return {"data": self._data}

class DummyClient:
    def __init__(self, tables):
        self.tables = tables
    def table(self, name):
        return DummyTable(self.tables.get(name, []))

def test_announcements_returned():
    rows = [
        {"id": 1, "title": "Welcome", "content": "Greetings", "created_at": "2025-01-01"}
    ]
    login_routes.get_supabase_client = lambda: DummyClient({"login_announcements": rows})
    result = asyncio.run(login_routes.get_announcements())
    assert result["announcements"][0]["title"] == "Welcome"
