from fastapi.testclient import TestClient
from backend.main import app
import backend.routers.logs as logs

client = TestClient(app)


class DummyTable:
    def __init__(self, store):
        self.store = store

    def insert(self, payload):
        self.store['payload'] = payload
        return self

    def execute(self):
        self.store['executed'] = True
        return {}


class DummyClient:
    def __init__(self, store):
        self.store = store

    def table(self, name):
        self.store['table'] = name
        return DummyTable(self.store)


def test_log_404_records(monkeypatch):
    store = {}
    monkeypatch.setattr(logs, 'get_supabase_client', lambda: DummyClient(store))
    resp = client.post('/api/logs/404', json={
        'path': '/missing',
        'referrer': '',
        'user_agent': 'evil<script>',
        'type': '404'
    })
    assert resp.status_code == 200
    assert store['table'] == 'client_errors'
    assert store['executed'] is True
    assert store['payload']['user_agent'] == 'evil&lt;script&gt;'
