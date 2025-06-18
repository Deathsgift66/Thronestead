from backend.routers import admin_news

class DummyResult:
    def __init__(self, data=None):
        self.data = data
        self.error = None
        self.status_code = 201

    def fetchall(self):
        return self.data or []

    def fetchone(self):
        return self.data[0] if isinstance(self.data, list) and self.data else None

class DummyTable:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.single_mode = False
        self.inserted = None

    def select(self, *_):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        self.single_mode = True
        return self

    def insert(self, record):
        self.inserted = record
        return self

    def execute(self):
        if self.inserted is not None:
            return DummyResult(self.inserted)
        if self.single_mode:
            return {"data": self.rows[0] if self.rows else None}
        return {"data": self.rows}

class DummyClient:
    def __init__(self):
        self.tables = {
            "users": DummyTable([{"display_name": "Admin"}]),
            "news_articles": DummyTable()
        }

    def table(self, name):
        return self.tables[name]

class DummyDB:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        if q.strip().lower().startswith("select is_admin"):
            return DummyResult([(True,)])
        return DummyResult()

    def commit(self):
        pass


def test_post_news_inserts_and_logs(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(admin_news, "get_supabase_client", lambda: client)
    db = DummyDB()
    payload = admin_news.NewsPayload(title="T", summary="S", content="C")
    res = admin_news.post_news(payload, admin_user_id="a1", db=db)
    assert res["status"] == "posted"
    assert client.tables["news_articles"].inserted["title"] == "T"
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)

