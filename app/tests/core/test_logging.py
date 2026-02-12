from app.core.logging import _scrub_sensitive_data, get_logger


def test_scrub_sensitive_data_redacts_known_fields():
    event = {
        "pin": "1234",
        "password": "supersecret",
        "access_token": "token123",
        "refresh_token": "refresh123",
        "raw_pin": "9999",
        "old_pin": "0000",
        "new_pin": "1111",
        "note": "safe",
    }

    redacted = _scrub_sensitive_data(None, "info", event)

    for key in [
        "pin",
        "password",
        "access_token",
        "refresh_token",
        "raw_pin",
        "old_pin",
        "new_pin",
    ]:
        assert redacted[key] == "[REDACTED]"

    assert redacted["note"] == "safe"


def test_scrub_sensitive_data_is_case_insensitive():
    event = {
        "PIN": "1234",
        "Password": "Secret",
        "Other": "value",
    }

    redacted = _scrub_sensitive_data(None, "info", event)

    assert redacted["PIN"] == "[REDACTED]"
    assert redacted["Password"] == "[REDACTED]"
    assert redacted["Other"] == "value"


def test_scrub_sensitive_data_handles_empty_event_dict():
    assert _scrub_sensitive_data(None, "info", {}) == {}


def test_get_logger_has_standard_levels():
    logger = get_logger("test_logger")

    for level in ("info", "warning", "error", "debug"):
        assert hasattr(logger, level)
