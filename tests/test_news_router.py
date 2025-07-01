# Comment
# Project Name: Thronestead©
# File Name: test_news_router.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
import pytest
from fastapi import HTTPException

from backend.routers import news


class DummyTable:
    def __init__(self, rows=None):
        self._rows = rows or []
        self._single = False

    def select(self, *_):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._single:
            return {"data": self._rows[0] if self._rows else None}
        return {"data": self._rows}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_invalid_user():
    client = DummyClient({"users": []})
    news.get_supabase_client = lambda: client
    with pytest.raises(HTTPException):
        news.articles(user_id="u1")


def test_returns_articles():
    rows = [
        {
            "id": 1,
            "title": "A",
            "summary": "S",
            "author_name": "B",
            "published_at": "2025-01-01",
        }
    ]
    tables = {"users": [{"user_id": "u1"}], "news_articles": rows}
    client = DummyClient(tables)
    news.get_supabase_client = lambda: client
    result = news.articles(user_id="u1")
    assert result["articles"][0]["title"] == "A"
