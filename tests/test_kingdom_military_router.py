# Project Name: Thronestead©
# File Name: test_kingdom_military_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import pytest
from fastapi import HTTPException

from backend.routers.kingdom_military import (
    RecruitPayload,
    get_current_user_id,
    get_state,
    history,
    queue,
    recruit,
    recruitable,
    summary,
)


def test_get_current_user_id_missing():
    with pytest.raises(HTTPException):
        get_current_user_id(None)


def test_summary_usable_slots():
    data = summary(user_id="u1")
    assert data["usable_slots"] == data["base_slots"] - data["used_slots"]


def test_recruit_flow():
    state = get_state()
    state["used_slots"] = 0
    state["queue"] = []
    recruit(RecruitPayload(unit_id=1, quantity=2), user_id="u1")
    assert state["used_slots"] == 2
    assert state["queue"][0]["unit_name"] == "Swordsman"
    assert "is_support" in state["queue"][0]


def test_recruitable_has_units():
    data = recruitable(user_id="u1")
    assert data["units"]


def test_queue_returns_list():
    state = get_state()
    state["queue"] = [{"unit_name": "Spearman", "quantity": 1, "is_support": False, "is_siege": False}]
    data = queue(user_id="u1")
    assert len(data["queue"]) == 1


def test_history_returns_list():
    state = get_state()
    state["history"] = [{"unit_name": "Archer", "quantity": 1}]
    data = history(user_id="u1")
    assert data["history"][0]["unit_name"] == "Archer"
