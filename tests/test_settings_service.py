from __future__ import annotations


def test_defaults_are_typed_correctly(settings_service):
    assert settings_service.get_bool("clipboard.monitoring_enabled") is True
    assert settings_service.get_int("clipboard.max_session_items") == 500
    assert settings_service.get_str("clipboard.copy_separator") == "New line"


def test_set_and_get_round_trip(settings_service):
    settings_service.set("clipboard.max_session_items", 250)
    assert settings_service.get_int("clipboard.max_session_items") == 250

    settings_service.set("hotkeys.enabled", False)
    assert settings_service.get_bool("hotkeys.enabled") is False

    settings_service.set("appearance.theme", "Dark")
    assert settings_service.get_str("appearance.theme") == "Dark"


def test_unknown_key_falls_back_to_default(settings_service):
    assert settings_service.get_bool("does.not.exist", True) is True
    assert settings_service.get_int("does.not.exist", 42) == 42
    assert settings_service.get_str("does.not.exist", "fallback") == "fallback"
