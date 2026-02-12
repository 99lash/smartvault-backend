"""
Helper functions for recording Prometheus metrics.

These functions provide a clean interface for use cases
to record metrics without importing Prometheus directly.

Clean Architecture:
    Infrastructure layer.
    Application layer (use cases) imports from here.
    This is the boundary between app and infrastructure.

Usage:
    from app.infrastructure.monitoring.helpers import track_vault_unlock

    track_vault_unlock(method="pin", success=True, duration_seconds=0.45)
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator, Literal

from app.infrastructure.monitoring import metrics


def track_vault_unlock(
    method: Literal["pin", "biometric"],
    success: bool,
    duration_seconds: float,
) -> None:
    """
    Record a vault unlock attempt.

    Args:
        method: Unlock method used (pin or biometric).
        success: Whether the unlock succeeded.
        duration_seconds: Time taken to process the request.
    """
    metrics.vault_unlocks_total.labels(
        method=method,
        success=str(success).lower(),
    ).inc()

    metrics.vault_unlock_duration_seconds.labels(
        method=method,
    ).observe(duration_seconds)


def track_vault_pin_set() -> None:
    """Record a successful vault PIN set operation."""
    metrics.vault_pins_set_total.inc()


def track_vault_member_added(role: str) -> None:
    """
    Record a vault member being added.

    Args:
        role: The role assigned to the new member.
    """
    metrics.vault_members_added_total.labels(
        role=role,
    ).inc()


def track_pin_lockout() -> None:
    """Record a PIN lockout event (security metric)."""
    metrics.pin_lockouts_total.inc()


def track_auth_failure(reason: str) -> None:
    """
    Record an authentication failure.

    Args:
        reason: Why authentication failed
                (invalid_credentials | expired_token | locked_out).
    """
    metrics.auth_failures_total.labels(
        reason=reason,
    ).inc()


@contextmanager
def track_duration(
    method: Literal["pin", "biometric"],
) -> Generator[None, None, None]:
    """
    Context manager to track unlock duration automatically.

    Usage:
        with track_duration(method="pin") as tracker:
            result = await use_case.execute(input)

    Args:
        method: Unlock method being tracked.

    Yields:
        None
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        metrics.vault_unlock_duration_seconds.labels(
            method=method,
        ).observe(duration)