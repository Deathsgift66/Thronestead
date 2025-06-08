from services.kingdom_title_service import award_title, list_titles, set_active_title, get_active_title


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.inserted = []
        self.select_rows = []
        self.updated = []
        self.check_row = None

    def execute(self, query, params=None):
        q = str(query).strip()
        params = params or {}
        if q.startswith("SELECT 1 FROM kingdom_titles"):
            return DummyResult(self.check_row)
        if q.startswith("INSERT INTO kingdom_titles"):
            self.inserted.append(params)
            return DummyResult()
        if q.startswith("SELECT title, awarded_at"):
            return DummyResult(rows=self.select_rows)
        if q.startswith("UPDATE kingdoms SET active_title"):
            self.updated.append(params)
            return DummyResult()
        if q.startswith("SELECT active_title"):
            return DummyResult(row=("Champion",))
        return DummyResult()

    def commit(self):
        pass


def test_award_title_inserts_when_new():
    db = DummyDB()
    db.check_row = None
    award_title(db, 1, "Defender")
    assert db.inserted[0]["title"] == "Defender"


def test_award_title_skips_existing():
    db = DummyDB()
    db.check_row = (1,)
    award_title(db, 1, "Defender")
    assert db.inserted == []


def test_list_titles_returns_rows():
    db = DummyDB()
    db.select_rows = [("Defender", "2025-06-09")]
    results = list_titles(db, 1)
    assert results[0]["title"] == "Defender"


def test_set_active_title_updates():
    db = DummyDB()
    set_active_title(db, 1, "Champion")
    assert db.updated[0]["title"] == "Champion"


def test_get_active_title():
    db = DummyDB()
    title = get_active_title(db, 1)
    assert title == "Champion"
