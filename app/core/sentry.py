"""
Sentry error tracking initialization.

SECURITY CONSIDERATIONS:
- Never send PII (passwords, PINs, tokens)
- Scrub sensitive data before sending
- Use appropriate sampling rates
"""

from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from app.core.settings import settings


def init_sentry() -> None:
    """
    Initialize Sentry error tracking.
    
    Only initializes if SENTRY_DSN is configured.
    Integrates with FastAPI, SQLAlchemy, and Redis.
    """
    if not settings.SENTRY_DSN:
        # Sentry not configured - skip initialization
        return
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        
        # Performance monitoring
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        
        # Privacy
        send_default_pii=settings.SENTRY_SEND_DEFAULT_PII,
        
        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        
        # Data scrubbing
        before_send=scrub_sensitive_data,
    )


def scrub_sensitive_data(event: dict, hint: dict) -> dict | None:
    """
    Scrub sensitive data before sending to Sentry.
    
    CRITICAL SECURITY FUNCTION:
    - Remove passwords, PINs, tokens
    - Redact sensitive headers
    - Strip sensitive query parameters
    
    Args:
        event: Sentry event dict
        hint: Additional context
        
    Returns:
        Scrubbed event or None to drop event
    """
    # Scrub request data
    if "request" in event:
        request = event["request"]
        
        # Scrub headers
        if "headers" in request:
            sensitive_headers = {
                "authorization",
                "cookie",
                "x-api-key",
                "x-auth-token",
                "x-admin-token",
            }
            request["headers"] = {
                k: "[REDACTED]" if k.lower() in sensitive_headers else v
                for k, v in request["headers"].items()
            }
        
        # Scrub query parameters
        if "query_string" in request:
            sensitive_params = {"pin", "password", "token", "secret"}
            query_string = request.get("query_string", "")
            if isinstance(query_string, str):
                # Check if any sensitive param in query string
                if any(param in query_string.lower() for param in sensitive_params):
                    request["query_string"] = "[REDACTED]"
        
        # Scrub POST data
        if "data" in request and isinstance(request["data"], dict):
            sensitive_fields = {
                "pin", 
                "password", 
                "old_pin", 
                "new_pin", 
                "raw_pin",
                "token",
                "access_token",
                "refresh_token",
                "secret",
            }
            for field in sensitive_fields:
                if field in request["data"]:
                    request["data"][field] = "[REDACTED]"
    
    # Scrub exception context
    if "exception" in event:
        for exception in event["exception"].get("values", []):
            # Remove sensitive data from exception messages
            if "value" in exception:
                msg = str(exception["value"]).lower()
                # Redact if message contains sensitive keywords
                sensitive_keywords = ["pin", "password", "token", "secret"]
                if any(keyword in msg for keyword in sensitive_keywords):
                    exception["value"] = "[Message contains sensitive data - redacted]"
    
    # Scrub extra context
    if "extra" in event:
        sensitive_keys = {"pin", "password", "token", "secret", "api_key"}
        for key in list(event["extra"].keys()):
            if key.lower() in sensitive_keys:
                event["extra"][key] = "[REDACTED]"
    
    return event