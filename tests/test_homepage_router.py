# Comment
# Project Name: Thronestead©
# File Name: test_homepage_router.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
from backend.routers import homepage


class DummyTable:
    def __init__(self, rows=None):
        self._rows = rows or []
        self._single = False

    def select(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def execute(self):
        return {"data": self._rows}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_featured_news_returns_rows():
    rows = [
        {"id": 1, "title": "Hello", "summary": "S", "published_at": "2025-01-01"},
        {"id": 2, "title": "World", "summary": "T", "published_at": "2025-01-02"},
    ]
    homepage.get_supabase_client = lambda: DummyClient({"news_articles": rows})
    result = homepage.featured_news()
    assert len(result["articles"]) == 2
    assert result["articles"][0]["title"] == "Hello"
