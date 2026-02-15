"""
API Keys screen - Create, list, and revoke API keys.
"""
from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Static, DataTable, Input, Checkbox

from smartvault_admin_tui.screens.base import BaseScreen


class APIKeysScreen(BaseScreen):
    """API key management screen."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
        ("c", "create", "Create"),
    ]
    
    DEFAULT_CSS = """
    APIKeysScreen {
        layout: vertical;
        overflow-y: auto;
    }
    
    APIKeysScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    APIKeysScreen .create-section {
        border: solid $success;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }
    
    APIKeysScreen .input-row {
        height: auto;
        min-height: 3;
        align-vertical: middle;
        margin-bottom: 1;
    }
    
    APIKeysScreen .input-row Label {
        width: auto;
        padding-right: 1;
    }
    
    APIKeysScreen .input-row Input {
        width: 1fr;
    }
    
    APIKeysScreen .key-display {
        border: solid $warning;
        padding: 1 2;
        margin: 1 0;
    }
    
    APIKeysScreen .key-value {
        width: 100%;
        text-align: center;
        margin: 1 0;
        background: blue;
        color: white;
        padding: 1;
        text-style: bold;
    }
    
    APIKeysScreen .warning-text {
        color: $warning;
    }
    
    APIKeysScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    
    APIKeysScreen .table-header {
        height: auto;
        min-height: 3;
        margin: 1 0;
        align-vertical: middle;
    }

    APIKeysScreen #keys-table {
        height: 1fr;
        min-height: 10;
        margin-top: 1;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, Any] | None = None
        self._active_only = True
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
        
        with Container():
            yield Label("Loading API keys...", id="loading")
            with Container(id="content", classes="hidden"):
                # Create section
                with Container(classes="create-section"):
                    yield Label("CREATE NEW API KEY", classes="section-title")
                    with Horizontal(classes="input-row"):
                        yield Label("Name:")
                        yield Input(placeholder="Key name", id="key-name-input")
                    with Horizontal(classes="input-row"):
                        yield Label("Expires (days):")
                        yield Input(placeholder="Never (leave empty)", id="expires-input", value="")
                    yield Button("Generate Key", id="create-btn", variant="success")
                
                # Key display (hidden by default)
                with Container(classes="key-display hidden", id="key-display"):
                    yield Label("⚠️ NEW KEY - Copy now! It will not be shown again.", classes="warning-text")
                    yield Input(placeholder="Key will appear here", id="new-key-value", classes="key-value")
                    with Horizontal():
                        yield Button("Copy", id="copy-btn")
                        yield Button("Close", id="close-key-btn")
                
                # Existing keys
                with Horizontal(classes="table-header"):
                    yield Label("EXISTING API KEYS", classes="section-title")
                    yield Checkbox("Active Only", value=True, id="active-only-checkbox")
                
                yield DataTable(id="keys-table")
                
                # Actions
                with Horizontal():
                    yield Button("Revoke Selected", id="revoke-btn", variant="error")
    
    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.run_worker(self.load_data())
    
    async def load_data(self) -> None:
        """Load API keys from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)
        
        try:
            loading.update("Loading API keys...")
            loading.remove_class("hidden")
            content.add_class("hidden")
            
            self._data = await self.api_client.list_api_keys(active_only=self._active_only)
            
            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")
            
        except Exception as e:
            loading.update(f"Error loading API keys: {e}")
            loading.add_class("error")
    
    def _render_data(self) -> None:
        """Render the loaded data."""
        if not self._data:
            return
        
        # Keys table
        table = self.query_one("#keys-table", DataTable)
        table.clear()
        table.add_columns("ID", "Name", "Created By", "Last Used", "Expires", "Status")
        
        for key in self._data.get("items", []):
            status = "🟢" if key.get("is_active") else "🔴"
            last_used = key.get("last_used_at") or "Never"
            expires = key.get("expires_at") or "Never"
            
            table.add_row(
                str(key.get("id", "")),
                key.get("name", ""),
                key.get("created_by", ""),
                str(last_used)[:19] if last_used != "Never" else last_used,
                str(expires)[:19] if expires != "Never" else expires,
                status,
            )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-btn":
            await self._create_key()
        elif event.button.id == "revoke-btn":
            await self._revoke_selected_key()
        elif event.button.id == "close-key-btn":
            self.query_one("#key-display", Container).add_class("hidden")
        elif event.button.id == "copy-btn":
            key_input = self.query_one("#new-key-value", Input)
            # Clipboard copying would go here
            self.notify("Key copied to clipboard!")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        if event.checkbox.id == "active-only-checkbox":
            self._active_only = event.value
            self.app.call_later(self.load_data)
    
    async def _create_key(self) -> None:
        """Create a new API key."""
        name_input = self.query_one("#key-name-input", Input)
        expires_input = self.query_one("#expires-input", Input)
        
        name = name_input.value.strip()
        if not name:
            self.notify("Please enter a name for the key", severity="error")
            return
        
        expires_in_days = None
        if expires_input.value.strip():
            try:
                expires_in_days = int(expires_input.value.strip())
            except ValueError:
                self.notify("Invalid expiry days", severity="error")
                return
        
        try:
            result = await self.api_client.create_api_key(name, expires_in_days)
            logger.info(f"API Key Created: {result}")
            
            # Show the new key
            key_display = self.query_one("#key-display", Container)
            key_input = self.query_one("#new-key-value", Input)
            
            plain_key = result.get("key")
            if not plain_key:
                plain_key = "ERROR: Key missing from response"
                self.notify("API returned success but key was missing!", severity="error")
            
            key_display.remove_class("hidden")
            key_input.value = str(plain_key)
            
            # Use notification as a backup visibility test
            self.notify(f"KEY: {plain_key}", title="Key Created", timeout=20)
            
            # Clear inputs
            name_input.value = ""
            expires_input.value = ""
            
            # Refresh list
            await self.load_data()

            
        except Exception as e:
            self.notify(f"Error creating key: {e}", severity="error")
    
    async def _revoke_selected_key(self) -> None:
        """Revoke the selected API key."""
        table = self.query_one("#keys-table", DataTable)
        cursor = table.cursor_coordinate
        
        if cursor.row < 0:
            self.notify("Please select a key to revoke", severity="warning")
            return
        
        # Get key ID from table
        row_data = table.get_row_at(cursor.row)
        key_id = int(row_data[0])
        
        try:
            await self.api_client.revoke_api_key(key_id)
            
            self.notify(f"API key {key_id} revoked")
            await self.load_data()
            
        except Exception as e:
            self.notify(f"Error revoking key: {e}", severity="error")
    
    def action_create(self) -> None:
        """Focus on create section."""
        self.query_one("#key-name-input", Input).focus()
