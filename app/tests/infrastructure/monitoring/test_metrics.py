"""
Tests for Prometheus metrics infrastructure.

Verifies that metrics are defined correctly and
helper functions record data as expected.
"""

import pytest
from prometheus_client import REGISTRY

from app.infrastructure.monitoring import metrics
from app.infrastructure.monitoring.helpers import (
    track_vault_unlock,
    track_vault_pin_set,
    track_vault_member_added,
    track_pin_lockout,
    track_auth_failure,
)


def _get_counter_value(counter, **labels) -> float:
    """Helper to get current counter value for given labels."""
    try:
        return counter.labels(**labels)._value.get()
    except Exception:
        return 0.0


def test_track_vault_unlock_success_increments_counter():
    """Successful unlock increments counter with success=true."""
    before = _get_counter_value(
        metrics.vault_unlocks_total,
        method="pin",
        success="true",
    )

    track_vault_unlock(method="pin", success=True, duration_seconds=0.1)

    after = _get_counter_value(
        metrics.vault_unlocks_total,
        method="pin",
        success="true",
    )

    assert after == before + 1


def test_track_vault_unlock_failure_increments_counter():
    """Failed unlock increments counter with success=false."""
    before = _get_counter_value(
        metrics.vault_unlocks_total,
        method="pin",
        success="false",
    )

    track_vault_unlock(method="pin", success=False, duration_seconds=0.05)

    after = _get_counter_value(
        metrics.vault_unlocks_total,
        method="pin",
        success="false",
    )

    assert after == before + 1


def test_track_vault_unlock_records_duration():
    """Unlock duration is recorded in histogram."""
    from prometheus_client import generate_latest
    
    # Record the sample
    track_vault_unlock(method="pin", success=True, duration_seconds=0.5)
    
    # Parse the Prometheus output
    output = generate_latest(metrics.vault_unlock_duration_seconds).decode("utf-8")
    
    # Verify the metric contains data
    assert 'vault_unlock_duration_seconds_bucket' in output or 'vault_unlock_duration_seconds_sum' in output
    
    # Extract and verify the sum value
    found = False
    for line in output.split('\n'):
        if 'vault_unlock_duration_seconds_sum' in line and 'method="pin"' in line:
            value = float(line.split()[-1])
            assert value > 0, "Duration sum should be positive"
            found = True
            break
    
    assert found, "Expected to find the histogram sum in output"


def test_track_vault_pin_set_increments_counter():
    """PIN set operation increments counter."""
    before = metrics.vault_pins_set_total._value.get()

    track_vault_pin_set()

    after = metrics.vault_pins_set_total._value.get()

    assert after == before + 1


def test_track_vault_member_added_by_role():
    """Member added counter is tracked by role."""
    before = _get_counter_value(
        metrics.vault_members_added_total,
        role="MEMBER",
    )

    track_vault_member_added(role="MEMBER")

    after = _get_counter_value(
        metrics.vault_members_added_total,
        role="MEMBER",
    )

    assert after == before + 1


def test_track_pin_lockout_increments_counter():
    """PIN lockout increments security counter."""
    before = metrics.pin_lockouts_total._value.get()

    track_pin_lockout()

    after = metrics.pin_lockouts_total._value.get()

    assert after == before + 1


def test_track_auth_failure_by_reason():
    """Auth failure is tracked by reason."""
    before = _get_counter_value(
        metrics.auth_failures_total,
        reason="invalid_credentials",
    )

    track_auth_failure(reason="invalid_credentials")

    after = _get_counter_value(
        metrics.auth_failures_total,
        reason="invalid_credentials",
    )

    assert after == before + 1


def test_metrics_exported_in_prometheus_format():
    """All custom metrics appear in Prometheus output."""
    from prometheus_client import generate_latest

    output = generate_latest(REGISTRY).decode("utf-8")

    assert "smartvault_vault_unlocks_total" in output
    assert "smartvault_vault_unlock_duration_seconds" in output
    assert "smartvault_vault_pins_set_total" in output
    assert "smartvault_vault_members_added_total" in output
    assert "smartvault_pin_lockouts_total" in output
    assert "smartvault_auth_failures_total" in output
    assert "smartvault_app_info" in output