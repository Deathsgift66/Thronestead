from backend.routers import legal


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self._ordered = self._data

    def select(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        self._ordered = sorted(self._data, key=lambda x: x.get("display_order", 0))
        return self

    def execute(self):
        return {"data": self._ordered}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_returns_sorted_docs():
    docs = [
        {"id": 2, "title": "B", "summary": "s", "url": "u", "display_order": 2},
        {"id": 1, "title": "A", "summary": "s", "url": "u", "display_order": 1},
    ]
    legal.get_supabase_client = lambda: DummyClient({"legal_documents": docs})
    result = legal.list_documents()
    assert result["documents"][0]["id"] == 1
    assert len(result["documents"]) == 2
