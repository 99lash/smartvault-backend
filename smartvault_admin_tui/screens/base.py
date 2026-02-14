from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from textual.screen import Screen
from textual.widgets import Label
from textual.binding import Binding

if TYPE_CHECKING:
    from smartvault_admin_tui.app import SmartVaultAdminApp
    from smartvault_admin_tui.api.client import APIClient

logger = logging.getLogger(__name__)

class BaseScreen(Screen):
    """Base screen with common functionality."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def action_back(self) -> None:
        """Default back action: Go to dashboard or previous screen."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Trigger a data refresh."""
        self.run_worker(self.load_data(), exclusive=True, group="refresh")

    @property
    def smart_app(self) -> "SmartVaultAdminApp":
        """Typed accessor for the main app."""
        return self.app  # type: ignore

    @property
    def api_client(self) -> "APIClient":
        """Access the shared API client."""
        client = self.smart_app.api_client
        if not client:
             raise RuntimeError("API Client not initialized")
        return client

    async def load_data(self) -> None:
        """Override this to load data."""
        pass

    def handle_error(self, error: Exception, title: str = "Error") -> None:
        """Standard error handling."""
        logger.error(f"{title}: {error}", exc_info=True)
        self.notify(str(error), title=title, severity="error", timeout=10)

    async def fetch_data(self, fetch_func: Callable[[], Awaitable[Any]]) -> Any | None:
        """Helper to fetch data with standardized error handling."""
        try:
            return await fetch_func()
        except Exception as e:
            self.handle_error(e, "Fetch Failed")
            return None
