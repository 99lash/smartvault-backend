"""Tests for Sentry settings configuration."""

import pytest
from pydantic import ValidationError


def test_sentry_dsn_optional(clean_settings_class):
    """Sentry DSN is optional (for local dev)."""
    Settings = clean_settings_class
    
    settings = Settings(
        SECRET_KEY="test-key-min-32-chars-long-12345",
        DATABASE_URL="postgresql://test",
        REDIS_URL="redis://test",
        # No SENTRY_DSN
    )
    assert settings.SENTRY_DSN is None


def test_sentry_environment_defaults_to_development(clean_settings_class):
    """Environment defaults to development."""
    Settings = clean_settings_class
    
    settings = Settings(
        SECRET_KEY="test-key-min-32-chars-long-12345",
        DATABASE_URL="postgresql://test",
        REDIS_URL="redis://test",
    )
    assert settings.SENTRY_ENVIRONMENT == "development"


def test_sentry_sample_rates_bounded(clean_settings_class):
    """Sample rates must be between 0.0 and 1.0."""
    Settings = clean_settings_class
    
    # Valid
    settings = Settings(
        SECRET_KEY="test-key-min-32-chars-long-12345",
        DATABASE_URL="postgresql://test",
        REDIS_URL="redis://test",
        SENTRY_TRACES_SAMPLE_RATE=0.5,
        SENTRY_PROFILES_SAMPLE_RATE=0.1,
    )
    assert settings.SENTRY_TRACES_SAMPLE_RATE == 0.5
    
    # Invalid (too high)
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="test-key-min-32-chars-long-12345",
            DATABASE_URL="postgresql://test",
            REDIS_URL="redis://test",
            SENTRY_TRACES_SAMPLE_RATE=1.5,
        )
    
    # Invalid (negative)
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="test-key-min-32-chars-long-12345",
            DATABASE_URL="postgresql://test",
            REDIS_URL="redis://test",
            SENTRY_PROFILES_SAMPLE_RATE=-0.1,
        )


def test_sentry_pii_defaults_to_false(clean_settings_class):
    """PII sending is disabled by default (security)."""
    Settings = clean_settings_class
    
    settings = Settings(
        SECRET_KEY="test-key-min-32-chars-long-12345",
        DATABASE_URL="postgresql://test",
        REDIS_URL="redis://test",
    )
    assert settings.SENTRY_SEND_DEFAULT_PII is False


def test_sentry_dsn_can_be_set(clean_settings_class):
    """Sentry DSN can be configured."""
    Settings = clean_settings_class
    
    test_dsn = "https://test@o123.ingest.sentry.io/456"
    settings = Settings(
        SECRET_KEY="test-key-min-32-chars-long-12345",
        DATABASE_URL="postgresql://test",
        REDIS_URL="redis://test",
        SENTRY_DSN=test_dsn,
    )
    assert settings.SENTRY_DSN == test_dsn