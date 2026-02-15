"""
Activity screen - Activity log with filters and pagination.
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Static, DataTable, Input

from smartvault_admin_tui.screens.base import BaseScreen
from smartvault_admin_tui.config import config


class ActivityScreen(BaseScreen):
    """Activity log screen with filters and pagination."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
        ("n", "next_page", "Next"),
        ("p", "prev_page", "Prev"),
    ]
    
    DEFAULT_CSS = """
    ActivityScreen {
        layout: vertical;
    }
    
    ActivityScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    ActivityScreen .filters-row {
        layout: horizontal;
        height: 3;
        margin: 1 0;
    }
    
    ActivityScreen .filter-input {
        width: 10;
        margin: 0 1;
    }
    
    ActivityScreen .summary-row {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }
    
    ActivityScreen .summary-item {
        padding: 0 2;
    }
    
    ActivityScreen #activity-table {
        height: 1fr;
    }
    
    ActivityScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    
    ActivityScreen .pagination {
        text-align: center;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, Any] | None = None
        self._hours = 24
        self._limit = config.default_page_size
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Loading activity...", id="loading")
            with Container(id="content", classes="hidden"):
                # Filters
                with Horizontal(classes="filters-row"):
                    yield Label("Hours:")
                    yield Input(value=str(self._hours), id="hours-input", classes="filter-input")
                    yield Label("Limit:")
                    yield Input(value=str(self._limit), id="limit-input", classes="filter-input")
                    yield Button("Apply", id="apply-btn")
                
                # Summary
                with Horizontal(classes="summary-row"):
                    yield Label("", id="summary-total", classes="summary-item")
                    yield Label("", id="summary-unlocks", classes="summary-item")
                    yield Label("", id="summary-failed", classes="summary-item")
                    yield Label("", id="summary-pin", classes="summary-item")
                
                # Activity table
                yield DataTable(id="activity-table")
                
                # Pagination
                with Horizontal(classes="pagination"):
                    yield Label("", id="pagination-info")
    
    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.run_worker(self.load_data())
    
    async def load_data(self) -> None:
        """Load activity data from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)
        
        try:
            loading.update("Loading activity...")
            loading.remove_class("hidden")
            content.add_class("hidden")
            
            self._data = await self.api_client.get_activity(hours=self._hours, limit=self._limit)
            
            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")
            
        except Exception as e:
            loading.update(f"Error loading activity: {e}")
            loading.add_class("error")
    
    def _render_data(self) -> None:
        """Render the loaded data."""
        if not self._data:
            return
        
        # Summary
        summary = self._data.get("summary", {})
        self.query_one("#summary-total", Label).update(f"Total: {summary.get('total_events', 0):,}")
        self.query_one("#summary-unlocks", Label).update(f"Unlocks: {summary.get('vault_unlocks', 0):,}")
        self.query_one("#summary-failed", Label).update(f"Failed: {summary.get('failed_unlocks', 0)}")
        self.query_one("#summary-pin", Label).update(f"PIN Ops: {summary.get('pin_operations', 0)}")
        
        # Table
        table = self.query_one("#activity-table", DataTable)
        table.clear()
        table.add_columns("Time", "Vault ID", "User ID", "Action", "Method", "Details")
        
        for entry in self._data.get("entries", []):
            created = entry.get("created_at", "")
            time_str = created.split("T")[1][:8] if "T" in created else created
            table.add_row(
                time_str,
                entry.get("vault_id", "")[:12],
                (entry.get("user_id") or "-")[:12],
                entry.get("action", ""),
                entry.get("method", ""),
                str(entry.get("metadata", ""))[:30],
            )
        
        # Pagination info
        self.query_one("#pagination-info", Label).update(
            f"Showing {len(self._data.get('entries', []))} events from last {self._hours}h"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply-btn":
            try:
                hours_input = self.query_one("#hours-input", Input)
                limit_input = self.query_one("#limit-input", Input)
                self._hours = int(hours_input.value)
                self._limit = min(int(limit_input.value), config.max_page_size)
                self.app.call_later(self.load_data)
            except ValueError:
                pass
    
    def action_refresh(self) -> None:
        """Refresh the activity data."""
        self.run_worker(self.load_data(), exclusive=True, group="refresh")
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_next_page(self) -> None:
        """Load next page (increase limit)."""
        self._limit = min(self._limit + config.default_page_size, config.max_page_size)
        self.app.call_later(self.load_data)
    
    def action_prev_page(self) -> None:
        """Load previous page (decrease limit)."""
        self._limit = max(self._limit - config.default_page_size, 10)
        self.app.call_later(self.load_data)
