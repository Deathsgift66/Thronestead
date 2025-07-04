from backend.routers import onboarding


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row

    def scalar(self):
        return self._row[0] if self._row else None


class DummyDB:
    def __init__(self, rows=None):
        self.rows = rows or {}
        self.calls = []

    def execute(self, query, params=None):
        q = str(query)
        self.calls.append((q, params))
        for key, value in self.rows.items():
            if key in q:
                if isinstance(value, tuple):
                    return DummyResult(value)
                return DummyResult((value,))
        return DummyResult(None)

    def commit(self):
        pass


def test_status_reports_flags():
    rows = {
        "FROM users": (1, False),
        "kingdom_villages": (1,),
        "kingdom_resources": (1,),
        "kingdom_troop_slots": (1,),
        "kingdom_nobles": (1,),
        "kingdom_knights": (1,),
        "kingdom_titles": (1,),
    }
    db = DummyDB(rows)
    result = onboarding.status(user_id="u1", db=db)
    assert result["kingdom"]
    assert result["village"]
    assert result["resources"]
    assert result["troop_slots"]
    assert result["noble"]
    assert result["knight"]
    assert result["title"]
    assert not result["complete"]


def test_create_noble_executes_insert():
    rows = {"FROM kingdoms": (1,)}
    db = DummyDB(rows)
    payload = onboarding.NoblePayload(noble_name="Alice")
    onboarding.create_noble(payload, user_id="u1", db=db)
    assert any("INSERT INTO kingdom_nobles" in q for q, _ in db.calls)
