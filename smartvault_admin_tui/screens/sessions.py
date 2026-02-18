"""
Sessions screen - Session statistics and user session revocation.
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Static, DataTable, Input

from smartvault_admin_tui.screens.base import BaseScreen


class SessionsScreen(BaseScreen):
    """Session management screen."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("escape", "back", "Back"),
    ]
    
    DEFAULT_CSS = """
    SessionsScreen {
        layout: vertical;
    }
    
    SessionsScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    SessionsScreen .stats-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
    }
    
    SessionsScreen .revoke-section {
        border: solid $warning;
        padding: 1 2;
        margin: 1 0;
    }
    
    SessionsScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    
    SessionsScreen #sessions-table {
        height: 1fr;
    }
    
    SessionsScreen .warning-text {
        color: $warning;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, Any] | None = None
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Loading sessions...", id="loading")
            with Container(id="content", classes="hidden"):
                # Stats section
                with Container(classes="stats-box"):
                    yield Label("SESSION STATISTICS", classes="section-title")
                    yield Label("", id="total-tokens")
                    yield Label("", id="checked-at")
                
                # Top users table
                yield Label("TOP USERS BY SESSION COUNT", classes="section-title")
                yield DataTable(id="sessions-table")
                
                # Revoke section
                with Container(classes="revoke-section"):
                    yield Label("REVOKE BY USER ID", classes="section-title")
                    with Horizontal():
                        yield Label("User ID:")
                        yield Input(placeholder="Enter user ID", id="user-id-input")
                        yield Button("Revoke All Sessions", id="revoke-btn")
                    yield Label("⚠️ This will force logout the user from all devices.", classes="warning-text")
                
                # Recent revocations
                yield Label("RECENT REVOCATIONS", classes="section-title")
                yield Label("", id="recent-revocations")
    
    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.run_worker(self.load_data())
    
    async def load_data(self) -> None:
        """Load session data from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)
        
        try:
            loading.update("Loading sessions...")
            loading.remove_class("hidden")
            content.add_class("hidden")
            
            self._data = await self.api_client.get_session_stats()
            
            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")
            
        except Exception as e:
            loading.update(f"Error loading sessions: {e}")
            loading.add_class("error")
    
    def _render_data(self) -> None:
        """Render the loaded data."""
        if not self._data:
            return
        
        # Stats
        self.query_one("#total-tokens", Label).update(
            f"Total Active Tokens: {self._data.get('total_active_tokens', 0):,}"
        )
        self.query_one("#checked-at", Label).update(
            f"Checked At: {self._data.get('checked_at', 'N/A')}"
        )
        
        # Top users table
        table = self.query_one("#sessions-table", DataTable)
        table.clear()
        table.add_columns("Rank", "User ID", "Sessions", "Action")
        
        for i, user in enumerate(self._data.get("top_users", []), 1):
            table.add_row(
                str(i),
                user.get("user_id", ""),
                str(user.get("token_count", 0)),
                "Revoke",
            )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "revoke-btn":
            user_id_input = self.query_one("#user-id-input", Input)
            user_id = user_id_input.value.strip()
            
            if not user_id:
                return
            
            try:
                result = await self.api_client.revoke_user_sessions(user_id)
                
                # Update recent revocations
                recent = self.query_one("#recent-revocations", Label)
                current = recent.renderable or ""
                new_entry = f"User {user_id}: {result.get('sessions_revoked', 0)} sessions revoked"
                recent.update(f"{new_entry}\n{current}")
                
                # Clear input
                user_id_input.value = ""
                
                # Refresh data
                await self.load_data()
                
            except Exception as e:
                self.query_one("#recent-revocations", Label).update(
                    f"Error: {e}"
                )
    
    def action_refresh(self) -> None:
        """Refresh the session data."""
        self.run_worker(self.load_data(), exclusive=True, group="refresh")
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
