"""Structured logging setup for the SmartVault backend."""

from __future__ import annotations

import logging
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from app.core.settings import settings


_SENSITIVE_FIELDS: set[str] = {
    "pin",
    "raw_pin",
    "old_pin",
    "new_pin",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "authorization",
}


def _scrub_sensitive_data(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive values using a case-insensitive key match."""
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_FIELDS:
            event_dict[key] = "[REDACTED]"
    return event_dict


def setup_logging() -> None:
    """Configure structlog for the current environment."""
    is_dev = settings.environment.lower() in {"development", "dev", "local"}

    renderer: structlog.types.Processor
    if is_dev:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    pre_chain: list[structlog.types.Processor] = [
        merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        _scrub_sensitive_data,
        timestamper,
    ]

    if not is_dev:
        pre_chain.append(structlog.processors.dict_tracebacks)

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=pre_chain,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[handler],
        force=True,
    )

    structlog.configure(
        processors=pre_chain + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name) if name else structlog.get_logger()
