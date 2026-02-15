from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Static

from smartvault_admin_tui.screens.base import BaseScreen


class NotificationsScreen(BaseScreen):
    """Screen for checking notification system status."""

    CSS = """
    NotificationsScreen {
        align: center middle;
    }

    .card {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-style: bold;
        text-align: center;
        margin-bottom: 2;
    }

    .metric-row {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }

    .metric {
        width: 1fr;
        content-align: center middle;
    }

    .metric-label {
        color: $text-muted;
    }

    .metric-value {
        text-style: bold;
    }

    .status-indicator {
        text-align: center;
        margin: 1 0;
        padding: 1;
        background: $surface-lighten-1;
    }
    
    .ok { color: $success; }
    .warning { color: $warning; }
    .critical { color: $error; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, Any] | None = None

    def compose(self) -> ComposeResult:
        with Container(classes="card"):
            yield Label("Email Notification Service", classes="title")
            
            # Status Indicator
            yield Static("Checking status...", id="status-indicator", classes="status-indicator")
            
            # Metrics
            yield Label("Today's Statistics", classes="section-title")
            with Horizontal(classes="metric-row"):
                with Vertical(classes="metric"):
                    yield Label("Sent", classes="metric-label")
                    yield Label("-", id="sent-count", classes="metric-value")
                
                with Vertical(classes="metric"):
                    yield Label("Failed", classes="metric-label")
                    yield Label("-", id="failed-count", classes="metric-value")

            yield Label("", id="meta-info", classes="text-muted")

    async def on_mount(self) -> None:
        self.run_worker(self.load_data())

    async def load_data(self) -> None:
        try:
            self.query_one("#status-indicator").update("↻ Loading...")
            
            # Fetch data using shared client
            self._data = await self.api_client.get_email_status()
            
            if self._data:
                self._render_data()
                
        except Exception as e:
            self.handle_error(e, "Notifications Error")
            self.query_one("#status-indicator").update("⚠ Connection Error")
            self.query_one("#status-indicator").add_class("critical")

    def _render_data(self) -> None:
        if not self._data:
            return

        status = self._data.get("status", "unknown")
        service = self._data.get("service", "smtp")
        sent = self._data.get("sent_today", 0)
        failed = self._data.get("failed_today", 0)
        checked_at = self._data.get("checked_at", "")

        # Update Status
        indicator = self.query_one("#status-indicator")
        indicator.update(f"● {service.upper()}: {status.upper()}")
        
        # Reset classes
        indicator.remove_class("ok")
        indicator.remove_class("warning")
        indicator.remove_class("critical")
        
        if status == "healthy":
            indicator.add_class("ok")
        elif status == "warning":
            indicator.add_class("warning")
        else:
            indicator.add_class("critical")

        # Update Metrics
        self.query_one("#sent-count").update(str(sent))
        self.query_one("#failed-count").update(str(failed))
        
        # Meta
        self.query_one("#meta-info").update(f"Last checked: {checked_at}")
