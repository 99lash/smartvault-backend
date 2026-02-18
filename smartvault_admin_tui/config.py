"""
Configuration for SmartVault Admin TUI.

Settings are loaded from environment variables with sensible defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Application configuration."""
    
    # API settings
    api_base_url: str
    admin_token: str
    
    # Refresh intervals (seconds)
    dashboard_refresh_interval: int
    diagnostics_refresh_interval: int
    
    # Pagination defaults
    default_page_size: int
    max_page_size: int
    
    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        return cls(
            api_base_url=os.getenv("SMARTVAULT_API_URL", "http://localhost:8000/api"),
            admin_token=os.getenv("ADMIN_API_TOKEN", ""),
            dashboard_refresh_interval=int(os.getenv("DASHBOARD_REFRESH_INTERVAL", "30")),
            diagnostics_refresh_interval=int(os.getenv("DIAGNOSTICS_REFRESH_INTERVAL", "60")),
            default_page_size=int(os.getenv("DEFAULT_PAGE_SIZE", "50")),
            max_page_size=int(os.getenv("MAX_PAGE_SIZE", "100")),
        )


# Global config instance
config = Config.from_env()
