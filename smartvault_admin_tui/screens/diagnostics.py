"""
Diagnostics screen - Redis, WebSocket, Database, and Email diagnostics.
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label, Static

from smartvault_admin_tui.api.client import APIClient
from smartvault_admin_tui.widgets.metric_card import ProgressBar


class DiagnosticsScreen(Screen):
    """System diagnostics screen."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
    ]
    
    DEFAULT_CSS = """
    DiagnosticsScreen {
        layout: vertical;
    }
    
    DiagnosticsScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    DiagnosticsScreen .diagnostic-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
    }
    
    DiagnosticsScreen .metric-row {
        layout: horizontal;
        height: auto;
    }
    
    DiagnosticsScreen .metric-label {
        width: 20;
    }
    
    DiagnosticsScreen .metric-value {
        color: $text;
    }
    
    DiagnosticsScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    
    DiagnosticsScreen .status-ok {
        color: $success;
    }
    
    DiagnosticsScreen .status-error {
        color: $error;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._redis: dict[str, Any] | None = None
        self._websockets: dict[str, Any] | None = None
        self._database: dict[str, Any] | None = None
        self._email: dict[str, Any] | None = None
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Loading diagnostics...", id="loading")
            with Container(id="content", classes="hidden"):
                # Redis
                with Container(classes="diagnostic-box"):
                    yield Label("REDIS", classes="section-title")
                    with Horizontal(classes="metric-row"):
                        yield Label("Status:", classes="metric-label")
                        yield Label("", id="redis-status", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Memory Used:", classes="metric-label")
                        yield Label("", id="redis-memory", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Total Keys:", classes="metric-label")
                        yield Label("", id="redis-keys", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Uptime:", classes="metric-label")
                        yield Label("", id="redis-uptime", classes="metric-value")
                    yield ProgressBar(id="redis-memory-bar")
                
                # WebSockets
                with Container(classes="diagnostic-box"):
                    yield Label("WEBSOCKETS", classes="section-title")
                    with Horizontal(classes="metric-row"):
                        yield Label("Total Users:", classes="metric-label")
                        yield Label("", id="ws-users", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Connections:", classes="metric-label")
                        yield Label("", id="ws-connections", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Total Vaults:", classes="metric-label")
                        yield Label("", id="ws-vaults", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Subscriptions:", classes="metric-label")
                        yield Label("", id="ws-subs", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Online Vaults:", classes="metric-label")
                        yield Label("", id="ws-online", classes="metric-value")
                
                # Database
                with Container(classes="diagnostic-box"):
                    yield Label("DATABASE", classes="section-title")
                    with Horizontal(classes="metric-row"):
                        yield Label("Status:", classes="metric-label")
                        yield Label("", id="db-status", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Pool Size:", classes="metric-label")
                        yield Label("", id="db-pool", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Checked Out:", classes="metric-label")
                        yield Label("", id="db-checked", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Overflow:", classes="metric-label")
                        yield Label("", id="db-overflow", classes="metric-value")
                    yield ProgressBar(id="db-pool-bar")
                
                # Email
                with Container(classes="diagnostic-box"):
                    yield Label("EMAIL SERVICE", classes="section-title")
                    with Horizontal(classes="metric-row"):
                        yield Label("Service:", classes="metric-label")
                        yield Label("", id="email-service", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Status:", classes="metric-label")
                        yield Label("", id="email-status", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Sent Today:", classes="metric-label")
                        yield Label("", id="email-sent", classes="metric-value")
                    with Horizontal(classes="metric-row"):
                        yield Label("Failed Today:", classes="metric-label")
                        yield Label("", id="email-failed", classes="metric-value")
    
    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        await self.load_data()
    
    async def load_data(self) -> None:
        """Load diagnostics data from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)
        
        try:
            loading.update("Loading diagnostics...")
            loading.remove_class("hidden")
            content.add_class("hidden")
            
            async with APIClient() as client:
                self._redis = await client.get_redis_diagnostics()
                self._websockets = await client.get_websocket_diagnostics()
                self._database = await client.get_database_diagnostics()
                self._email = await client.get_email_status()
            
            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")
            
        except Exception as e:
            loading.update(f"Error loading diagnostics: {e}")
            loading.add_class("error")
    
    def _render_data(self) -> None:
        """Render the loaded data."""
        # Redis
        if self._redis:
            status = self._redis.get("status", "unknown")
            status_class = "status-ok" if status == "healthy" or self._redis.get("connected") else "status-error"
            self.query_one("#redis-status", Label).update(status)
            self.query_one("#redis-status", Label).set_class(True, status_class)
            self.query_one("#redis-memory", Label).update(f"{self._redis.get('memory_used_mb', 0):.2f} MB")
            self.query_one("#redis-keys", Label).update(str(self._redis.get('total_keys', 0)))
            self.query_one("#redis-uptime", Label).update(self._format_uptime(self._redis.get('uptime_seconds', 0)))
            # Memory bar (assume 512MB max)
            self.query_one("#redis-memory-bar", ProgressBar).update_value(self._redis.get('memory_used_mb', 0))
        
        # WebSockets
        if self._websockets:
            self.query_one("#ws-users", Label).update(str(self._websockets.get('total_users', 0)))
            self.query_one("#ws-connections", Label).update(str(self._websockets.get('total_user_connections', 0)))
            self.query_one("#ws-vaults", Label).update(str(self._websockets.get('total_vaults', 0)))
            self.query_one("#ws-subs", Label).update(str(self._websockets.get('subscriptions', 0)))
            online = self._websockets.get('online_vaults', [])
            self.query_one("#ws-online", Label).update(
                ", ".join(online[:5]) + (f" (+{len(online)-5} more)" if len(online) > 5 else "")
            )
        
        # Database
        if self._database:
            status = self._database.get("status", "unknown")
            status_class = "status-ok" if status == "healthy" else "status-error"
            self.query_one("#db-status", Label).update(status)
            self.query_one("#db-status", Label).set_class(True, status_class)
            pool_size = self._database.get('pool_size', 0)
            checked_out = self._database.get('checked_out', 0)
            self.query_one("#db-pool", Label).update(str(pool_size))
            self.query_one("#db-checked", Label).update(str(checked_out))
            self.query_one("#db-overflow", Label).update(str(self._database.get('overflow', 0)))
            # Pool bar
            self.query_one("#db-pool-bar", ProgressBar).update_value(checked_out)
        
        # Email
        if self._email:
            self.query_one("#email-service", Label).update(self._email.get('service', 'unknown'))
            status = self._email.get("status", "unknown")
            status_class = "status-ok" if status == "healthy" else "status-error"
            self.query_one("#email-status", Label).update(status)
            self.query_one("#email-status", Label).set_class(True, status_class)
            self.query_one("#email-sent", Label).update(str(self._email.get('sent_today', 0)))
            self.query_one("#email-failed", Label).update(str(self._email.get('failed_today', 0)))
    
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in human-readable format."""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    def action_refresh(self) -> None:
        """Refresh the diagnostics."""
        self.app.call_later(self.load_data)
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
