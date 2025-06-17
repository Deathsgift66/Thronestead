# Project Name: Thronestead©
# File Name: test_account_settings_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.routers import account_settings

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
        self.profile_row = None
        self.sessions = []
        self.current_row = None
        self.custom_row = None
        self.updated = None
        self.custom_updated = None
        self.settings_rows = []
        self.setting_updates = []
    def execute(self, query, params=None):
        q = str(query).strip()
        params = params or {}
        if q.startswith("SELECT u.username"):
            return DummyResult(row=self.profile_row)
        if q.startswith("SELECT session_id"):
            return DummyResult(rows=self.sessions)
        if q.startswith("SELECT display_name"):
            return DummyResult(row=self.current_row)
        if q.startswith("SELECT motto"):
            return DummyResult(row=self.custom_row)
        if q.startswith("SELECT setting_key"):
            return DummyResult(rows=self.settings_rows)
        if q.startswith("UPDATE users SET"):
            self.updated = params
            return DummyResult()
        if q.startswith("INSERT INTO user_customization"):
            self.custom_updated = params
            return DummyResult()
        if q.startswith("INSERT INTO user_setting_entries"):
            self.setting_updates.append(params)
            return DummyResult()
        return DummyResult()
    def commit(self):
        pass

def test_load_profile_returns_security_fields():
    db = DummyDB()
    db.profile_row = (
        "hero",
        "Hero",
        "pic.png",
        "a@example.com",
        "NA",
        "Kingdom",
        "Alliance",
        "Hi",
        "Bio",
        "parchment",
        "banner.png",
        1,
        False,
        None,
    )
    db.settings_rows = [
        ("ip_login_alerts", "true"),
        ("email_login_confirmations", "false"),
    ]
    result = account_settings.load_profile(user_id="u1", db=db)
    assert result["ip_login_alerts"] is True
    assert result["email_login_confirmations"] is False

def test_update_profile_updates_security_fields():
    db = DummyDB()
    db.current_row = ("Old", "old.png")
    db.settings_rows = [
        ("ip_login_alerts", "true"),
        ("email_login_confirmations", "false"),
    ]
    db.custom_row = ("M", "B", "p", "ban")
    payload = account_settings.UpdatePayload(
        display_name="New",
        ip_login_alerts=False,
        email_login_confirmations=True,
    )
    account_settings.update_profile(payload, user_id="u1", db=db)
    assert db.updated["dn"] == "New"
    assert db.setting_updates[0]["val"] == "false"
    assert db.setting_updates[1]["val"] == "true"
