# Project Name: Kingmakers Rise©
# File Name: test_policies_laws_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers import policies_laws


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self.updated = []
        self._filtered = self._data
        self._ordered = self._data
        self._single = False

    def select(self, *_args):
        return self

    def eq(self, field, value):
        self._filtered = [r for r in self._data if r.get(field) == value]
        self._ordered = self._filtered
        return self

    def order(self, field, *_args, **_kwargs):
        self._ordered = sorted(self._filtered, key=lambda x: x.get(field, 0))
        return self

    def single(self):
        self._single = True
        return self

    def update(self, data):
        self.updated.append(data)
        return self

    def execute(self):
        class Result:
            def __init__(self, data):
                self.data = data

        if self._single:
            return Result(self._filtered[0] if self._filtered else None)
        return Result(self._ordered)


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return self.tables.setdefault(name, DummyTable())


def test_catalogue_sorted():
    entries = [
        {"id": 2, "type": "policy"},
        {"id": 1, "type": "law"},
    ]
    client = DummyClient({"policies_laws_catalogue": DummyTable(entries)})
    policies_laws.get_supabase_client = lambda: client
    result = policies_laws.catalogue(user_id="u1")
    assert result["entries"][0]["id"] == 1

def test_user_settings():
    client = DummyClient({"users": DummyTable([{"user_id": "u1", "active_policy": 3, "active_laws": [1]}])})
    policies_laws.get_supabase_client = lambda: client
    result = policies_laws.user_settings(user_id="u1")
    assert result["active_policy"] == 3
    assert result["active_laws"] == [1]


def test_updates_call_update():
    table = DummyTable([{}])
    client = DummyClient({"users": table})
    policies_laws.get_supabase_client = lambda: client
    policies_laws.update_policy(policies_laws.UpdatePolicyPayload(policy_id=5), user_id="u1")
    policies_laws.update_laws(policies_laws.UpdateLawsPayload(law_ids=[1, 2]), user_id="u1")
    assert table.updated[0] == {"active_policy": 5}
    assert table.updated[1] == {"active_laws": [1, 2]}
