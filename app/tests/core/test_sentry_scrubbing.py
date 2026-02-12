"""Tests for Sentry data scrubbing (SECURITY CRITICAL)."""

import pytest

from app.core.sentry import scrub_sensitive_data


def test_scrub_authorization_header():
    """Authorization header is redacted."""
    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer secret-token-12345",
                "Content-Type": "application/json",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["headers"]["Authorization"] == "[REDACTED]"
    assert scrubbed["request"]["headers"]["Content-Type"] == "application/json"


def test_scrub_cookie_header():
    """Cookie header is redacted."""
    event = {
        "request": {
            "headers": {
                "Cookie": "session=abc123; user=john",
                "User-Agent": "Mozilla/5.0",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["headers"]["Cookie"] == "[REDACTED]"
    assert scrubbed["request"]["headers"]["User-Agent"] == "Mozilla/5.0"


def test_scrub_admin_token_header():
    """X-Admin-Token header is redacted."""
    event = {
        "request": {
            "headers": {
                "X-Admin-Token": "admin-secret-token",
                "Accept": "application/json",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["headers"]["X-Admin-Token"] == "[REDACTED]"


def test_scrub_pin_in_post_data():
    """PIN in POST data is redacted."""
    event = {
        "request": {
            "data": {
                "pin": "123456",
                "vault_id": "vault-123",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["data"]["pin"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["vault_id"] == "vault-123"


def test_scrub_password_in_post_data():
    """Password in POST data is redacted."""
    event = {
        "request": {
            "data": {
                "email": "user@example.com",
                "password": "super-secret-password",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["data"]["password"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["email"] == "user@example.com"


def test_scrub_raw_pin_in_post_data():
    """raw_pin field is redacted."""
    event = {
        "request": {
            "data": {
                "vault_id": "vault-123",
                "raw_pin": "654321",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["data"]["raw_pin"] == "[REDACTED]"


def test_scrub_token_in_post_data():
    """Token fields are redacted."""
    event = {
        "request": {
            "data": {
                "user_id": "user-123",
                "token": "jwt-token-abc",
                "access_token": "access-xyz",
                "refresh_token": "refresh-123",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["data"]["token"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["access_token"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["refresh_token"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["user_id"] == "user-123"


def test_scrub_sensitive_exception_message():
    """Exception messages containing sensitive data are redacted."""
    event = {
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "Invalid PIN: 123456 for vault xyz",
                }
            ]
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert "123456" not in scrubbed["exception"]["values"][0]["value"]
    assert "[Message contains sensitive data - redacted]" in scrubbed["exception"]["values"][0]["value"]


def test_scrub_password_in_exception():
    """Exception with password in message is redacted."""
    event = {
        "exception": {
            "values": [
                {
                    "type": "AuthError",
                    "value": "Password verification failed for user",
                }
            ]
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["exception"]["values"][0]["value"] == "[Message contains sensitive data - redacted]"


def test_scrub_query_string_with_token():
    """Query strings with tokens are redacted."""
    event = {
        "request": {
            "query_string": "vault_id=123&token=secret-token"
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["query_string"] == "[REDACTED]"


def test_scrub_extra_context():
    """Extra context with sensitive keys is redacted."""
    event = {
        "extra": {
            "user_id": "user-123",
            "pin": "123456",
            "password": "secret",
            "metadata": {"safe": "data"},
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["extra"]["pin"] == "[REDACTED]"
    assert scrubbed["extra"]["password"] == "[REDACTED]"
    assert scrubbed["extra"]["user_id"] == "user-123"
    assert scrubbed["extra"]["metadata"] == {"safe": "data"}


def test_no_scrubbing_for_safe_data():
    """Safe data is not scrubbed."""
    event = {
        "request": {
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
            "data": {
                "vault_name": "My Vault",
                "role": "MEMBER",
            }
        }
    }
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed["request"]["headers"]["User-Agent"] == "Mozilla/5.0"
    assert scrubbed["request"]["data"]["vault_name"] == "My Vault"
    assert scrubbed["request"]["data"]["role"] == "MEMBER"


def test_scrubbing_handles_missing_fields():
    """Scrubbing doesn't crash on missing fields."""
    event = {
        "request": {}
    }
    
    # Should not raise
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed is not None


def test_scrubbing_handles_empty_event():
    """Scrubbing handles completely empty event."""
    event = {}
    
    scrubbed = scrub_sensitive_data(event, {})
    
    assert scrubbed == {}