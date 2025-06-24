import backend.battle_engine.resolver_full as resolver

class DummyDB:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((str(query).lower(), params))
        return []

def test_process_unit_combat_applies_morale(monkeypatch):
    db = DummyDB()
    monkeypatch.setattr(resolver, "db", db)
    attacker = {
        "movement_id": 1,
        "kingdom_id": 1,
        "position_x": 0,
        "position_y": 0,
        "quantity": 10,
        "morale": 100,
    }
    defender = {
        "movement_id": 2,
        "kingdom_id": 2,
        "position_x": 0,
        "position_y": 1,
        "quantity": 8,
        "morale": 100,
    }
    resolver.process_unit_combat(attacker, [attacker, defender], [["plains"]], 1, 1, "kingdom")

    update_def = db.queries[0]
    assert "update unit_movements" in update_def[0]
    # params: remaining qty, new morale, remaining qty, id
    assert update_def[1][0] == 0
    assert update_def[1][1] == 90.0

    update_att = db.queries[1]
    assert update_att[1] == (100.0, 1)

    insert = db.queries[2]
    assert "insert into combat_logs" in insert[0]
    # morale shift parameter is at index 8
    assert insert[1][8] == -10.0
