# Project Name: Thronestead©
# File Name: test_kingdom_achievement_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from services.kingdom_achievement_service import award_achievement, list_achievements


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
        self.check_rows = []
        self.reward = None
        self.honor_reward = 0
        self.list_rows = []
        self.prestige_updates = []
        self.history_logs = []

    def execute(self, query, params=None):
        q = str(query).strip()
        params = params or {}
        if q.startswith("SELECT 1 FROM kingdom_achievements"):
            return DummyResult(self.check_rows.pop(0) if self.check_rows else None)
        if q.startswith("INSERT INTO kingdom_achievements"):
            self.inserted.append(params)
            return DummyResult()
        if "SELECT reward, prestige_reward, name, honor_reward" in q:
            return DummyResult((self.reward, 5, "First Gold", self.honor_reward))
        if "SELECT reward FROM kingdom_achievement_catalogue" in q:
            return DummyResult((self.reward,))
        if q.startswith("UPDATE kingdoms SET prestige_score"):
            self.prestige_updates.append(params)
            return DummyResult()
        if q.startswith("SELECT user_id FROM kingdoms"):
            return DummyResult(row=("u1",))
        if q.startswith("INSERT INTO kingdom_history_log"):
            self.history_logs.append(params)
            return DummyResult()
        if "FROM kingdom_achievement_catalogue" in q and "LEFT JOIN" in q:
            return DummyResult(rows=self.list_rows)
        return DummyResult()

    def commit(self):
        pass


def test_award_new_achievement(monkeypatch):
    db = DummyDB()
    db.check_rows = [None]
    db.reward = {"gold": 100}
    db.honor_reward = 1

    called = {}
    import services.kingdom_achievement_service as kas
    kas_get = lambda rid: "Defender" if rid == 1 else None
    kas_award = lambda _db, kid, title: called.update({"kid": kid, "title": title})
    monkeypatch.setattr(kas, "get_title_name_from_id", kas_get)
    monkeypatch.setattr(kas, "award_title", kas_award)

    reward = award_achievement(db, 1, "first_gold")
    assert reward == {"gold": 100}
    assert db.inserted[0]["kid"] == 1
    assert len(db.prestige_updates) == 1
    assert len(db.history_logs) == 1
    assert db.history_logs[0]["etype"] == "ACHIEVEMENT_UNLOCKED"
    assert db.history_logs[0]["details"] == "Earned First Gold"
    assert called["title"] == "Defender"


def test_award_existing_returns_none():
    db = DummyDB()
    db.check_rows = [(1,)]
    reward = award_achievement(db, 1, "first_gold")
    assert reward is None
    assert db.inserted == []
    assert db.prestige_updates == []
    assert db.history_logs == []


def test_list_achievements_filters_hidden():
    db = DummyDB()
    db.list_rows = [
        (
            "first_gold",
            "First Gold",
            "Earn 1000",
            "economic",
            {"gold": 100},
            5,
            False,
            None,
        ),
        ("secret", "Secret", "Hidden details", "exploration", {}, 0, True, None),
        ("battle", "Battle", "Win", "military", {}, 10, False, "2025-01-01"),
    ]
    results = list_achievements(db, 1)
    codes = [r["achievement_code"] for r in results]
    assert "first_gold" in codes
    assert "battle" in codes
    assert "secret" not in codes
