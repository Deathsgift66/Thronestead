from backend.routers import login_routes
from fastapi.responses import JSONResponse
import json

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
    login_routes.get_supabase_client = lambda: DummyClient({"announcements": rows})
    resp = login_routes.get_announcements()
    assert isinstance(resp, JSONResponse)
    data = json.loads(resp.body.decode())
    assert data["announcements"][0]["title"] == "Welcome"
