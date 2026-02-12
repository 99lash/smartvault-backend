"""
Prometheus metric definitions for SmartVault.

All metrics are defined here as module-level singletons.
Prometheus client handles registration automatically.

Clean Architecture:
    Infrastructure layer only.
    No domain or application layer imports.

Metric Categories:
    1. System metrics   - Auto-instrumented via FastAPI instrumentator
    2. Business metrics - Custom counters/histograms for key operations
    3. Security metrics - Tracking suspicious activity
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Info


# =============================================================================
# SYSTEM METRICS
# Auto-instrumented by prometheus-fastapi-instrumentator:
#   - http_requests_total{method, handler, status}
#   - http_request_duration_seconds{method, handler}
#   - http_requests_inprogress{method, handler}
# =============================================================================


# =============================================================================
# BUSINESS METRICS
# =============================================================================

vault_unlocks_total = Counter(
    "smartvault_vault_unlocks_total",
    "Total vault unlock attempts",
    ["method", "success"],  # method: pin | biometric, success: true | false
)

vault_unlock_duration_seconds = Histogram(
    "smartvault_vault_unlock_duration_seconds",
    "Time taken to process a vault unlock request",
    ["method"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

vault_pins_set_total = Counter(
    "smartvault_vault_pins_set_total",
    "Total vault PIN set operations",
)

vault_members_added_total = Counter(
    "smartvault_vault_members_added_total",
    "Total vault members added",
    ["role"],  # role: OWNER | MEMBER | VIEWER
)

# =============================================================================
# SECURITY METRICS
# =============================================================================

pin_lockouts_total = Counter(
    "smartvault_pin_lockouts_total",
    "Total PIN lockout events triggered",
)

auth_failures_total = Counter(
    "smartvault_auth_failures_total",
    "Total authentication failures",
    ["reason"],  # reason: invalid_credentials | expired_token | locked_out
)

# =============================================================================
# APPLICATION INFO
# =============================================================================

app_info = Info(
    "smartvault_app",
    "SmartVault application metadata",
)


def set_app_info(version: str, environment: str) -> None:
    """
    Set static application metadata.

    Called once at startup via main.py.

    Args:
        version: Application version string.
        environment: Deployment environment (development/staging/production).
    """
    app_info.info({
        "version": version,
        "environment": environment,
    })