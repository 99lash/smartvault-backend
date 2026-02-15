"""
Security screen - Security alerts and rate limiting dashboard.
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, DataTable
from smartvault_admin_tui.screens.base import BaseScreen
from smartvault_admin_tui.widgets.alert_card import AlertList
from smartvault_admin_tui.widgets.metric_card import ProgressBar


class SecurityScreen(BaseScreen):
    """Security center screen with alerts and rate limiting."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
        ("l", "rate_limits", "Rate Limits"),
    ]
    
    DEFAULT_CSS = """
    SecurityScreen {
        layout: vertical;
    }
    
    SecurityScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    SecurityScreen .status-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
    }
    
    SecurityScreen .metrics-row {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }
    
    SecurityScreen .metrics-column {
        width: 1fr;
        padding: 0 1;
    }
    
    SecurityScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._alerts_data: dict[str, Any] | None = None
        self._rate_limits_data: dict[str, Any] | None = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()  # Base functionality
        
        with Container():
            yield Label("Loading security data...", id="loading")
            with Container(id="content", classes="hidden"):
                # Status section
                with Container(classes="status-box"):
                    yield Label("SECURITY STATUS", classes="section-title")
                    yield Label("", id="status-text")
                
                # Active alerts
                yield Label("ACTIVE ALERTS", classes="section-title")
                yield AlertList(id="alerts-list")
                
                # 24-hour metrics
                yield Label("24-HOUR METRICS", classes="section-title")
                with Horizontal(classes="metrics-row"):
                    with Vertical(classes="metrics-column"):
                        yield Label("Failed Unlocks", classes="section-title")
                        yield Label("", id="failed-1h")
                        yield Label("", id="failed-24h")
                        yield ProgressBar(id="failed-progress")
                    with Vertical(classes="metrics-column"):
                        yield Label("PIN Lockouts", classes="section-title")
                        yield Label("", id="lockouts-24h")
                        yield Label("", id="lockouts-threshold")
                        yield ProgressBar(id="lockouts-progress")
                
                # Rate limiting
                yield Label("RATE LIMITING", classes="section-title")
                with Horizontal(classes="metrics-row"):
                    yield Label("", id="rate-limit-summary")
                yield DataTable(id="violators-table")
    
    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.run_worker(self.load_data())
    
    async def load_data(self) -> None:
        """Load security data from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)
        
        try:
            loading.update("Loading security data...")
            loading.remove_class("hidden")
            content.add_class("hidden")
            
            # Use shared client from BaseScreen
            self._alerts_data = await self.api_client.get_security_alerts()
            self._rate_limits_data = await self.api_client.get_rate_limits()
            
            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")
            
        except Exception as e:
            loading.update(f"Error loading security data: {e}")
            loading.add_class("error")
    
    def _render_data(self) -> None:
        """Render the loaded data."""
        if not self._alerts_data:
            return
        
        # Status
        status = self._alerts_data.get("status", "ok")
        icons = {"ok": "🟢", "warning": "🟡", "critical": "🔴"}
        self.query_one("#status-text", Label).update(
            f"{icons.get(status, '⚪')} Status: {status.upper()}"
        )
        
        # Alerts
        alerts = self._alerts_data.get("active_alerts", [])
        self.query_one("#alerts-list", AlertList).update_alerts(alerts)
        
        # 24h metrics
        last_24h = self._alerts_data.get("last_24h", {})
        failed_1h = last_24h.get("failed_unlocks_1h", 0)
        failed_24h = last_24h.get("failed_unlocks_24h", 0)
        lockouts = last_24h.get("pin_lockouts_24h", 0)
        
        self.query_one("#failed-1h", Label).update(f"Last Hour: {failed_1h}")
        self.query_one("#failed-24h", Label).update(f"Last 24 Hours: {failed_24h}")
        self.query_one("#lockouts-24h", Label).update(f"Last 24 Hours: {lockouts}")
        self.query_one("#lockouts-threshold", Label).update("Warning Threshold: 3 | Critical: 10")
        
        # Progress bars (warning threshold = 5 for failed, 3 for lockouts)
        self.query_one("#failed-progress", ProgressBar).update_value(min(failed_1h, 20))
        self.query_one("#lockouts-progress", ProgressBar).update_value(min(lockouts, 10))
        
        # Rate limits
        if self._rate_limits_data:
            total = self._rate_limits_data.get("total_active_keys", 0)
            by_category = self._rate_limits_data.get("by_category", {})
            cat_str = " | ".join(f"{k}: {v}" for k, v in by_category.items())
            self.query_one("#rate-limit-summary", Label).update(
                f"Active Keys: {total} | Categories: {cat_str}"
            )
            
            # Violators table
            table = self.query_one("#violators-table", DataTable)
            table.clear()
            
            # Avoid re-adding columns when the table is reused
            if len(table.columns) == 0:
                table.add_columns("Key", "Count", "TTL (s)")
            for v in self._rate_limits_data.get("top_violators", []):
                table.add_row(
                    v.get("key", "")[:40],
                    str(v.get("current_count", 0)),
                    str(v.get("ttl_seconds", 0)),
                )
    
    def action_rate_limits(self) -> None:
        """Focus on rate limits section."""
        table = self.query_one("#violators-table", DataTable)
        table.focus()
