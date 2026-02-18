"""
Header widget with status badge and title.
"""
from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Label, Static


class StatusBadge(Static):
    """A colored status indicator."""
    
    def __init__(self, status: str = "ok", **kwargs) -> None:
        super().__init__(**kwargs)
        self.status = status
        self.update_status(status)
    
    def update_status(self, status: str) -> None:
        """Update the status display."""
        self.status = status
        icons = {
            "ok": "🟢",
            "warning": "🟡",
            "critical": "🔴",
        }
        self.update(icons.get(status, "⚪"))


class ClockDisplay(Static):
    """A clock that updates every second."""
    
    def on_mount(self) -> None:
        self.update_time()
        self.set_interval(1, self.update_time)
    
    def update_time(self) -> None:
        self.update(datetime.now().strftime("%H:%M:%S"))


class AdminHeader(Widget):
    """Header widget with title, status badge, and clock."""
    
    DEFAULT_CSS = """
    AdminHeader {
        dock: top;
        width: 100%;
        height: 1;
        background: $surface;
        color: $text;
    }
    
    AdminHeader Horizontal {
        width: 100%;
        height: 1;
    }
    
    AdminHeader .title {
        text-align: left;
        padding: 0 2;
    }
    
    AdminHeader .status {
        text-align: center;
        padding: 0 2;
    }
    
    AdminHeader .clock {
        text-align: right;
        padding: 0 2;
    }
    """
    
    def __init__(self, title: str = "SmartVault Admin Console", **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"🔐 {self.title}", classes="title")
            yield Label("", id="status-label", classes="status")
            yield ClockDisplay(classes="clock")
    
    def on_mount(self) -> None:
        self.set_interval(1, self._update_status)
    
    def _update_status(self) -> None:
        """Update status display from app state."""
        try:
            app = self.app
            if hasattr(app, "overall_status"):
                status_label = self.query_one("#status-label", Label)
                icons = {"ok": "🟢 OK", "warning": "🟡 WARNING", "critical": "🔴 CRITICAL"}
                status_label.update(icons.get(app.overall_status, "⚪ UNKNOWN"))
        except Exception:
            pass
    
    def set_status(self, status: str) -> None:
        """Set the overall status display."""
        status_label = self.query_one("#status-label", Label)
        icons = {"ok": "🟢 OK", "warning": "🟡 WARNING", "critical": "🔴 CRITICAL"}
        status_label.update(icons.get(status, "⚪ UNKNOWN"))
