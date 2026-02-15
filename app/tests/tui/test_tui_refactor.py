import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from smartvault_admin_tui.app import SmartVaultAdminApp
from smartvault_admin_tui.api.client import APIClient

@pytest.mark.asyncio
async def test_api_client_reuse():
    """Verify shared APIClient reuses httpx connection."""
    mock_httpx = AsyncMock()
    # Mocking httpx.AsyncClient instance
    client = APIClient(client=mock_httpx)
    
    # Client property should return the injected instance
    assert client.client is mock_httpx
    
    # Mock return value
    mock_httpx.get.return_value.status_code = 200
    mock_httpx.get.return_value.json.return_value = {"status": "ok"}
    
    await client.ping()
    mock_httpx.get.assert_called_once()
    
    # Close shouldn't close injected client unless owned (check implementation)
    # Actually implementation says _own_client=False if injected.
    await client.close()
    mock_httpx.aclose.assert_not_called()

@pytest.mark.asyncio
async def test_app_lifecycle_client():
    """Verify App initializes and cleans up client."""
    # Mock class to return an AsyncMock instance when instantiated
    mock_instance = AsyncMock()
    with patch("httpx.AsyncClient", return_value=mock_instance) as mock_client_cls:
        app = SmartVaultAdminApp()
        async with app.run_test() as pilot:
            # Client should be initialized
            assert app.api_client is not None
            assert app.http_client is mock_instance
            
        # Cleanup happened (on_unmount called aclose)
        mock_instance.aclose.assert_called()

@pytest.mark.asyncio
async def test_notifications_screen_render():
    """Verify NotificationsScreen renders and fetches data."""
    
    # Mock the API response
    mock_response = {
        "service": "smtp",
        "status": "operational",
        "sent_today": 42,
        "failed_today": 0,
        "checked_at": "2023-01-01T12:00:00Z"
    }

    # Prevent real network calls
    with patch("httpx.AsyncClient", return_value=AsyncMock()) as mock_client:
        app = SmartVaultAdminApp()
        
        async with app.run_test() as pilot:
            # Mock the client on the running app
            # Replace the method on the instance
            app.api_client.get_email_status = AsyncMock(return_value=mock_response)
            
            # Navigate to notifications
            await pilot.press("ctrl+n")
            
            # Wait for worker
            await pilot.pause()
            
            # Check current screen
            assert type(app.screen).__name__ == "NotificationsScreen"
            
            # Check rendered content (e.g. sent count 42)
            sent_label = app.screen.query_one("#sent-count")
            
            # Verify API interaction occurred
            app.api_client.get_email_status.assert_called_once()
            
            # Verify widget exists and is visible
            assert sent_label.visible
