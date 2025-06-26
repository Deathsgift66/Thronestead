# Project Name: Thronestead©
# File Name: test_moderation.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from services.moderation import classify_text, has_reserved_username, is_clean


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

