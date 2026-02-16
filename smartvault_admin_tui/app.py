"""
SmartVault Admin Console - Main Textual Application.

A terminal user interface for managing SmartVault internal operations.

Usage:
    python -m smartvault_admin_tui.app
    
Or with Textual CLI:
    textual run smartvault_admin_tui/app.py
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header

from smartvault_admin_tui.config import config
from smartvault_admin_tui.screens.dashboard import DashboardScreen
from smartvault_admin_tui.screens.security import SecurityScreen
from smartvault_admin_tui.screens.activity import ActivityScreen
from smartvault_admin_tui.screens.sessions import SessionsScreen
from smartvault_admin_tui.screens.api_keys import APIKeysScreen
from smartvault_admin_tui.screens.diagnostics import DiagnosticsScreen
from smartvault_admin_tui.screens.audit import AuditScreen
from smartvault_admin_tui.screens.notifications import NotificationsScreen
from smartvault_admin_tui.screens.trends import TrendsScreen
import httpx
from smartvault_admin_tui.api.client import APIClient


class SmartVaultAdminApp(App):
    """SmartVault Admin Console TUI Application."""
    
    TITLE = "SmartVault Admin Console"
    SUB_TITLE = "Internal Operations Dashboard"
    
    CSS = """
    Screen {
        padding: 1 2;
    }
    
    .hidden {
        display: none;
    }
    
    .error {
        color: $error;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+d", "dashboard", "Dashboard", show=True),
        Binding("ctrl+s", "security", "Security", show=True),
        Binding("ctrl+a", "activity", "Activity", show=True),
        Binding("ctrl+r", "sessions", "Sessions", show=True),
        Binding("ctrl+k", "api_keys", "API Keys", show=True),
        Binding("ctrl+x", "diagnostics", "Diagnostics", show=True),
        Binding("ctrl+u", "audit", "Audit", show=True),
        Binding("ctrl+n", "notifications", "Notifications", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("question_mark", "help", "Help", show=True),
        Binding("ctrl+t", "trends", "Trends", show=True),
    ]
    
    SCREENS = {
        "dashboard": DashboardScreen,
        "security": SecurityScreen,
        "activity": ActivityScreen,
        "sessions": SessionsScreen,
        "api_keys": APIKeysScreen,
        "diagnostics": DiagnosticsScreen,
        "audit": AuditScreen,
        "notifications": NotificationsScreen,
        "trends": TrendsScreen,
    }
    


    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.overall_status: str = "ok"
        self.http_client: httpx.AsyncClient | None = None
        self.api_client: APIClient | None = None
    
    def compose(self) -> ComposeResult:
        """Create the app layout."""
        yield Header()
        yield Container(id="main-container")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Mount the dashboard screen on startup."""
        self.http_client = httpx.AsyncClient(
            base_url=config.api_base_url,
            headers={"X-Admin-Token": config.admin_token},
            timeout=30.0,
        )
        self.api_client = APIClient(client=self.http_client)
        self.push_screen("dashboard")

    async def on_unmount(self) -> None:
        """Cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()
    
    def action_dashboard(self) -> None:
        """Navigate to dashboard screen."""
        self.push_screen("dashboard")
    
    def action_security(self) -> None:
        """Navigate to security screen."""
        self.push_screen("security")
    
    def action_activity(self) -> None:
        """Navigate to activity screen."""
        self.push_screen("activity")
    
    def action_sessions(self) -> None:
        """Navigate to sessions screen."""
        self.push_screen("sessions")
    
    def action_api_keys(self) -> None:
        """Navigate to API keys screen."""
        self.push_screen("api_keys")
    
    def action_diagnostics(self) -> None:
        """Navigate to diagnostics screen."""
        self.push_screen("diagnostics")
    
    def action_audit(self) -> None:
        """Navigate to audit screen."""
        self.push_screen("audit")

    def action_notifications(self) -> None:
        """Navigate to notifications screen."""
        self.push_screen("notifications")
    
    def action_trends(self) -> None:
        """Navigate to trends screen."""
        self.push_screen("trends")
        
    def action_help(self) -> None:
        """Show help screen."""
        self.notify(
            "Key Bindings:\n"
            "Ctrl+D - Dashboard\n"
            "Ctrl+S - Security\n"
            "Ctrl+A - Activity\n"
            "Ctrl+R - Sessions\n"
            "Ctrl+K - API Keys\n"
            "Ctrl+X - Diagnostics\n"
            "Ctrl+T - Trends\n"
            "Ctrl+U - Audit\n"
            "Ctrl+Q - Quit",
            title="Help",
            timeout=10,
        )
   

def main() -> None:
    """Main entry point."""
    if not config.admin_token:
        print("Error: ADMIN_API_TOKEN environment variable is not set.")
        print("Please set it before running the admin console:")
        print("  export ADMIN_API_TOKEN='your-admin-token'")
        return
    
    app = SmartVaultAdminApp()
    app.run()


if __name__ == "__main__":
    main()
