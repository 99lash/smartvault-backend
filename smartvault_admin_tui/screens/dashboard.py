from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, DataTable

# Removed direct APIClient import as it comes from BaseScreen
from smartvault_admin_tui.screens.base import BaseScreen
from smartvault_admin_tui.widgets.metric_card import MetricCard, MetricRow
from smartvault_admin_tui.widgets.alert_card import AlertList

class DashboardScreen(BaseScreen):
    """Main dashboard screen with overview metrics."""
    
    BINDINGS = [
        # BaseScreen provides 'refresh' (r) and 'back' (escape)
        ("s", "security", "Security"),
        ("a", "activity", "Activity"),
        ("ctrl+n", "notifications", "Notifications"),
    ]
    
    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
    }
    
    DashboardScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    DashboardScreen .status-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
    }
    
    DashboardScreen .metrics-container {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }
    
    DashboardScreen .metrics-column {
        width: 1fr;
        padding: 0 1;
    }
    
    DashboardScreen .activity-table {
        height: 10;
        margin-top: 1;
    }
    
    DashboardScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    
    DashboardScreen #error {
        text-align: center;
        padding: 2;
        color: $error;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, Any] | None = None
        self._activity: dict[str, Any] | None = None
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Loading dashboard...", id="loading")
            with Container(id="content", classes="hidden"):
                # Status section
                with Container(classes="status-box"):
                    yield Label("OVERALL STATUS", classes="section-title")
                    yield Label("", id="status-text")
                    yield Label("", id="generated-at")
                
                # Business metrics
                yield Label("BUSINESS METRICS", classes="section-title")
                with Horizontal(classes="metrics-container"):
                    with Vertical(classes="metrics-column"):
                        yield Label("👥 Users", classes="section-title")
                        yield Label("", id="users-total")
                        yield Label("", id="users-today")
                        yield Label("", id="users-week")
                    with Vertical(classes="metrics-column"):
                        yield Label("📦 Vaults", classes="section-title")
                        yield Label("", id="vaults-total")
                        yield Label("", id="vaults-pin")
                        yield Label("", id="vaults-status")
                    with Vertical(classes="metrics-column"):
                        yield Label("👤 Members", classes="section-title")
                        yield Label("", id="members-total")
                        yield Label("", id="members-roles")
                
                # Security section
                yield Label("SECURITY (24h)", classes="section-title")
                with Horizontal(classes="metrics-container"):
                    with Vertical(classes="metrics-column"):
                        yield Label("", id="sec-status")
                        yield Label("", id="sec-failed-1h")
                        yield Label("", id="sec-failed-24h")
                        yield Label("", id="sec-lockouts")
                
                # Activity section
                yield Label("ACTIVITY (24h)", classes="section-title")
                with Horizontal(classes="metrics-container"):
                    with Vertical(classes="metrics-column"):
                        yield Label("", id="act-total")
                        yield Label("", id="act-unlocks")
                        yield Label("", id="act-failed")
                        yield Label("", id="act-pin")
                
                # Recent activity
                yield Label("RECENT ACTIVITY", classes="section-title")
                yield DataTable(id="activity-table", classes="activity-table")
    
    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        # Base class handles client access
        self.run_worker(self.load_data())
    
    async def load_data(self) -> None:
        """Load dashboard data from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)
        
        try:
            loading.update("Loading dashboard...")
            loading.remove_class("hidden")
            content.add_class("hidden")
            
            # Use shared client directly
            self._data = await self.api_client.get_ops_summary()
            self._activity = await self.api_client.get_activity(hours=24, limit=5)
            
            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")
            
        except Exception as e:
            self.handle_error(e, "Dashboard Load Error")
            loading.update(f"Error: {e}")
            loading.add_class("error")

    def _render_data(self) -> None:
        """Render the loaded data."""
        if not self._data:
            return
        
        # Update app status
        self.smart_app.overall_status = self._data.get("overall_status", "ok")
        
        # Status section
        status = self._data.get("overall_status", "ok")
        icons = {"ok": "🟢", "warning": "🟡", "critical": "🔴"}
        self.query_one("#status-text", Label).update(
            f"{icons.get(status, '⚪')} Status: {status.upper()}"
        )
        self.query_one("#generated-at", Label).update(
            f"Generated: {self._data.get('generated_at', 'N/A')}"
        )
        
        # Business metrics
        business = self._data.get("business", {})
        users = business.get("users", {})
        vaults = business.get("vaults", {})
        members = business.get("members", {})
        
        self.query_one("#users-total", Label).update(f"Total: {users.get('total', 0):,}")
        self.query_one("#users-today", Label).update(f"New Today: {users.get('new_today', 0):,}")
        self.query_one("#users-week", Label).update(f"New Week: {users.get('new_this_week', 0):,}")
        
        self.query_one("#vaults-total", Label).update(f"Total: {vaults.get('total', 0):,}")
        self.query_one("#vaults-pin", Label).update(f"With PIN: {vaults.get('with_pin', 0):,}")
        by_status = vaults.get("by_status", {})
        status_str = " | ".join(f"{k}: {v}" for k, v in by_status.items())
        self.query_one("#vaults-status", Label).update(f"By Status: {status_str}")
        
        self.query_one("#members-total", Label).update(f"Authorizations: {members.get('total_authorizations', 0):,}")
        by_role = members.get("by_role", {})
        roles_str = " | ".join(f"{k}: {v}" for k, v in by_role.items())
        self.query_one("#members-roles", Label).update(f"By Role: {roles_str}")
        
        # Security
        security = self._data.get("security", {})
        sec_status = security.get("status", "ok")
        self.query_one("#sec-status", Label).update(f"Status: {icons.get(sec_status, '⚪')} {sec_status.upper()}")
        self.query_one("#sec-failed-1h", Label).update(f"Failed Unlocks (1h): {security.get('failed_unlocks_1h', 0)}")
        self.query_one("#sec-failed-24h", Label).update(f"Failed Unlocks (24h): {security.get('failed_unlocks_24h', 0)}")
        self.query_one("#sec-lockouts", Label).update(f"PIN Lockouts (24h): {security.get('pin_lockouts_24h', 0)}")
        
        # Activity
        activity = self._data.get("activity", {})
        self.query_one("#act-total", Label).update(f"Total Events: {activity.get('total_events', 0):,}")
        self.query_one("#act-unlocks", Label).update(f"Vault Unlocks: {activity.get('vault_unlocks', 0):,}")
        self.query_one("#act-failed", Label).update(f"Failed Unlocks: {activity.get('failed_unlocks', 0)}")
        self.query_one("#act-pin", Label).update(f"PIN Operations: {activity.get('pin_operations', 0)}")
        
        # Recent activity table
        table = self.query_one("#activity-table", DataTable)
        table.clear()
        
        # Check if columns exist already to avoid errors (DataTable is stateful if reused)
        if len(table.columns) == 0:
             table.add_columns("Time", "Vault", "User", "Action", "Details")
        
        if self._activity:
            for entry in self._activity.get("entries", []):
                created = entry.get("created_at", "")
                time_str = created.split("T")[1][:8] if "T" in created else created
                table.add_row(
                    time_str,
                    entry.get("vault_id", "")[:8],
                    entry.get("user_id", "")[:8] if entry.get("user_id") else "-",
                    entry.get("action", ""),
                    str(entry.get("metadata", ""))[:30],
                )
    
    def action_security(self) -> None:
        """Navigate to security screen."""
        self.smart_app.push_screen("security")
    
    def action_activity(self) -> None:
        """Navigate to activity screen."""
        self.smart_app.push_screen("activity")

    def action_notifications(self) -> None:
        """Navigate to notifications screen."""
        self.smart_app.push_screen("notifications")
