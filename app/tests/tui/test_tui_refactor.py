import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from smartvault_admin_tui.app import SmartVaultAdminApp
from smartvault_admin_tui.api.client import APIClient

@pytest.mark.asyncio
async def test_api_client_reuse():
    """Verify shared APIClient reuses httpx connection."""
    mock_httpx = AsyncMock()
    client = APIClient(client=mock_httpx)
    
    assert client.client is mock_httpx

    await client.close()
    mock_httpx.aclose.assert_not_called()

@pytest.mark.asyncio
async def test_app_lifecycle_client():
    """Verify App initializes and cleans up client."""
    mock_instance = AsyncMock()
    with (
        patch.object(APIClient, "get_ops_summary", AsyncMock(return_value={})),
        patch.object(APIClient, "get_activity", AsyncMock(return_value={})),
        patch("httpx.AsyncClient", return_value=mock_instance),
    ):
        app = SmartVaultAdminApp()
        async with app.run_test() as pilot:
            assert app.api_client is not None
            assert app.http_client is mock_instance

        mock_instance.aclose.assert_called()

@pytest.mark.asyncio
async def test_notifications_screen_render():
    """Verify NotificationsScreen renders and fetches data."""
    
    # Mock the API response
    mock_response = {
        "service": "smtp",
        "status": "healthy",
        "sent_today": 42,
        "failed_today": 0,
        "checked_at": "2023-01-01T12:00:00Z"
    }
    
    with (
        patch.object(APIClient, "get_ops_summary", AsyncMock(return_value={})),
        patch.object(APIClient, "get_activity", AsyncMock(return_value={})),
        patch.object(APIClient, "get_email_status", AsyncMock(return_value=mock_response)),
    ):
        app = SmartVaultAdminApp()
        
        async with app.run_test() as pilot:
            await pilot.press("ctrl+n")
            await pilot.pause()
            
            assert type(app.screen).__name__ == "NotificationsScreen"
            
            sent_label = app.screen.query_one("#sent-count")
            
            app.api_client.get_email_status.assert_called_once()
            assert sent_label.visible
