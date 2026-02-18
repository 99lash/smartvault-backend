"""
Alert card widget for displaying security alerts.
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, Static


class AlertCard(Widget):
    """A card displaying a security alert."""
    
    DEFAULT_CSS = """
    AlertCard {
        width: 100%;
        height: auto;
        border: solid $warning;
        padding: 1 2;
        margin: 1 0;
    }
    
    AlertCard.critical {
        border: solid $error;
    }
    
    AlertCard.warning {
        border: solid $warning;
    }
    
    AlertCard.low {
        border: solid $success;
    }
    
    AlertCard .alert-severity {
        text-style: bold;
    }
    
    AlertCard .alert-severity.critical {
        color: $error;
    }
    
    AlertCard .alert-severity.high {
        color: $warning;
    }
    
    AlertCard .alert-severity.medium {
        color: $accent;
    }
    
    AlertCard .alert-severity.low {
        color: $success;
    }
    
    AlertCard .alert-message {
        margin-top: 1;
    }
    
    AlertCard .alert-meta {
        color: $text-muted;
        margin-top: 1;
    }
    """
    
    def __init__(
        self, 
        alert: dict[str, Any],
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._alert = alert
        self.add_class(alert.get("severity", "warning"))
    
    def compose(self) -> ComposeResult:
        severity = self._alert.get("severity", "warning").upper()
        alert_type = self._alert.get("type", "unknown")
        message = self._alert.get("message", "")
        count = self._alert.get("count", 0)
        threshold = self._alert.get("threshold", 0)
        window = self._alert.get("window", "?")
        
        yield Label(f"⚠️ {severity}: {alert_type}", classes=f"alert-severity {severity.lower()}")
        yield Label(message, classes="alert-message")
        yield Label(f"Count: {count} | Threshold: {threshold} | Window: {window}", classes="alert-meta")


class AlertList(Widget):
    """A list of alert cards."""
    
    DEFAULT_CSS = """
    AlertList {
        width: 100%;
        height: auto;
    }
    """
    
    def __init__(self, alerts: list[dict[str, Any]] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._alerts = alerts or []
    
    def compose(self) -> ComposeResult:
        if not self._alerts:
            yield Label("✓ No active alerts", classes="no-alerts")
        else:
            for alert in self._alerts:
                yield AlertCard(alert)
    
    def update_alerts(self, alerts: list[dict[str, Any]]) -> None:
        """Update the alert list."""
        self._alerts = alerts
        # Remove existing children
        for child in list(self.children):
            child.remove()
        # Add new children
        if not alerts:
            self.mount(Label("✓ No active alerts", classes="no-alerts"))
        else:
            for alert in alerts:
                self.mount(AlertCard(alert))
