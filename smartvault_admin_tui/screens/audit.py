"""
Audit screen - Admin audit log with filters and pagination.
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static, DataTable, Input

from smartvault_admin_tui.api.client import APIClient
from smartvault_admin_tui.config import config


class AuditScreen(Screen):
    """Admin audit log screen."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
        ("n", "next_page", "Next"),
        ("p", "prev_page", "Prev"),
    ]
    
    DEFAULT_CSS = """
    AuditScreen {
        layout: vertical;
    }
    
    AuditScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    AuditScreen .filters-row {
        layout: horizontal;
        height: 3;
        margin: 1 0;
    }
    
    AuditScreen .filter-input {
        width: 15;
        margin: 0 1;
    }
    
    AuditScreen #audit-table {
        height: 1fr;
    }
    
    AuditScreen .details-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
    }
    
    AuditScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    
    AuditScreen .pagination {
        text-align: center;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, Any] | None = None
        self._page = 1
        self._limit = config.default_page_size
        self._action_filter: str | None = None
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Loading audit logs...", id="loading")
            with Container(id="content", classes="hidden"):
                # Filters
                with Horizontal(classes="filters-row"):
                    yield Label("Page:")
                    yield Input(value=str(self._page), id="page-input", classes="filter-input")
                    yield Label("Limit:")
                    yield Input(value=str(self._limit), id="limit-input", classes="filter-input")
                    yield Label("Action:")
                    yield Input(value="", placeholder="All", id="action-input", classes="filter-input")
                    yield Button("Apply", id="apply-btn")
                
                # Audit table
                yield DataTable(id="audit-table")
                
                # Pagination
                with Horizontal(classes="pagination"):
                    yield Label("", id="pagination-info")
                
                # Details box
                with Container(classes="details-box"):
                    yield Label("ENTRY DETAILS", classes="section-title")
                    yield Label("", id="details-content")
    
    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        await self.load_data()
    
    async def load_data(self) -> None:
        """Load audit logs from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)
        
        try:
            loading.update("Loading audit logs...")
            loading.remove_class("hidden")
            content.add_class("hidden")
            
            async with APIClient() as client:
                self._data = await client.get_audit_logs(
                    page=self._page,
                    limit=self._limit,
                    action=self._action_filter,
                )
            
            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")
            
        except Exception as e:
            loading.update(f"Error loading audit logs: {e}")
            loading.add_class("error")
    
    def _render_data(self) -> None:
        """Render the loaded data."""
        if not self._data:
            return
        
        # Table
        table = self.query_one("#audit-table", DataTable)
        table.clear()
        table.add_columns("ID", "Action", "Target Type", "Target ID", "Created At")
        
        for item in self._data.get("items", []):
            created = item.get("created_at", "")
            created_str = str(created)[:19] if created else ""
            
            table.add_row(
                str(item.get("id", "")),
                item.get("action", ""),
                item.get("target_type", ""),
                item.get("target_id", "") or "-",
                created_str,
            )
        
        # Pagination
        total = self._data.get("total", 0)
        pages = self._data.get("pages", 1)
        self.query_one("#pagination-info", Label).update(
            f"Showing {len(self._data.get('items', []))} of {total} entries | Page {self._page} of {pages}"
        )
    
    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row selection to show details."""
        if not self._data:
            return
        
        items = self._data.get("items", [])
        if event.row_index < len(items):
            item = items[event.row_index]
            details = self.query_one("#details-content", Label)
            
            details_text = f"""ID:         {item.get('id', '')}
Action:     {item.get('action', '')}
Target:     {item.get('target_type', '')} / {item.get('target_id', '-')}
IP Address: {item.get('ip_address', '-')}
Details:    {item.get('details', {})}
Created:    {item.get('created_at', '')}"""
            
            details.update(details_text)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply-btn":
            try:
                page_input = self.query_one("#page-input", Input)
                limit_input = self.query_one("#limit-input", Input)
                action_input = self.query_one("#action-input", Input)
                
                self._page = max(1, int(page_input.value))
                self._limit = min(int(limit_input.value), config.max_page_size)
                self._action_filter = action_input.value.strip() or None
                
                self.app.call_later(self.load_data)
            except ValueError:
                pass
    
    def action_refresh(self) -> None:
        """Refresh the audit logs."""
        self.app.call_later(self.load_data)
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_next_page(self) -> None:
        """Go to next page."""
        if self._data and self._page < self._data.get("pages", 1):
            self._page += 1
            self.query_one("#page-input", Input).value = str(self._page)
            self.app.call_later(self.load_data)
    
    def action_prev_page(self) -> None:
        """Go to previous page."""
        if self._page > 1:
            self._page -= 1
            self.query_one("#page-input", Input).value = str(self._page)
            self.app.call_later(self.load_data)
