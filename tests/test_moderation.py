# Project Name: Thronestead©
# File Name: test_moderation.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

import pytest
from services.moderation import (
    classify_text,
    has_reserved_username,
    is_clean,
    contains_malicious_link,
    validate_clean_text,
    validate_username,
)


def test_classify_hate_speech():
    res = classify_text("You are a nigger")
    assert res["hate_speech"]
    assert not res["sexual_content"]


def test_reserved_username_detection():
    assert has_reserved_username("Admin123")
    assert has_reserved_username("dev0")
    assert not has_reserved_username("peasant")


def test_is_clean_passes():
    assert is_clean("Greetings, traveler")


def test_personal_info_detection():
    res = classify_text("contact me at test@example.com")
    assert res["personal_info"]


def test_phone_number_detection():
    res = classify_text("call me at 123-456-7890")
    assert res["personal_info"]


def test_malicious_link_detection():
    assert contains_malicious_link("visit http://example.com now")


def test_validate_clean_text_raises():
    with pytest.raises(ValueError):
        validate_clean_text("watch porn here")


def test_validate_username_checks_reserved():
    with pytest.raises(ValueError):
        validate_username("Admin")

