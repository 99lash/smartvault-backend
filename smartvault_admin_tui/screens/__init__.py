"""Screens module."""
from smartvault_admin_tui.screens.dashboard import DashboardScreen
from smartvault_admin_tui.screens.security import SecurityScreen
from smartvault_admin_tui.screens.activity import ActivityScreen
from smartvault_admin_tui.screens.sessions import SessionsScreen
from smartvault_admin_tui.screens.api_keys import APIKeysScreen
from smartvault_admin_tui.screens.diagnostics import DiagnosticsScreen
from smartvault_admin_tui.screens.audit import AuditScreen

__all__ = [
    "DashboardScreen",
    "SecurityScreen",
    "ActivityScreen",
    "SessionsScreen",
    "APIKeysScreen",
    "DiagnosticsScreen",
    "AuditScreen",
]
