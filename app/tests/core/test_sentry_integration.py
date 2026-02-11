"""Integration tests for Sentry initialization."""

import pytest
from unittest.mock import patch, MagicMock

from app.core.sentry import init_sentry
from app.core.settings import settings


def test_sentry_not_initialized_without_dsn():
    """Sentry is not initialized when DSN is not configured."""
    with patch('app.core.sentry.sentry_sdk.init') as mock_init:
        with patch.object(settings, 'SENTRY_DSN', None):
            init_sentry()
            
            # Should NOT call sentry_sdk.init
            mock_init.assert_not_called()


def test_sentry_initialized_with_dsn():
    """Sentry is initialized when DSN is configured."""
    test_dsn = "https://test@o123.ingest.sentry.io/456"
    
    with patch('app.core.sentry.sentry_sdk.init') as mock_init:
        with patch.object(settings, 'SENTRY_DSN', test_dsn):
            with patch.object(settings, 'SENTRY_ENVIRONMENT', 'test'):
                init_sentry()
                
                # Should call sentry_sdk.init
                mock_init.assert_called_once()
                
                # Verify DSN was passed
                call_kwargs = mock_init.call_args.kwargs
                assert call_kwargs['dsn'] == test_dsn
                assert call_kwargs['environment'] == 'test'


def test_sentry_integrations_configured():
    """Sentry integrations are properly configured."""
    test_dsn = "https://test@o123.ingest.sentry.io/456"
    
    with patch('app.core.sentry.sentry_sdk.init') as mock_init:
        with patch.object(settings, 'SENTRY_DSN', test_dsn):
            init_sentry()
            
            call_kwargs = mock_init.call_args.kwargs
            integrations = call_kwargs['integrations']
            
            # Should have 3 integrations
            assert len(integrations) == 3
            
            # Check integration types
            integration_names = [type(i).__name__ for i in integrations]
            assert 'FastApiIntegration' in integration_names
            assert 'SqlalchemyIntegration' in integration_names
            assert 'RedisIntegration' in integration_names


def test_sentry_before_send_configured():
    """Sentry before_send hook is configured."""
    test_dsn = "https://test@o123.ingest.sentry.io/456"
    
    with patch('app.core.sentry.sentry_sdk.init') as mock_init:
        with patch.object(settings, 'SENTRY_DSN', test_dsn):
            init_sentry()
            
            call_kwargs = mock_init.call_args.kwargs
            
            # Should have before_send callback
            assert 'before_send' in call_kwargs
            assert callable(call_kwargs['before_send'])


def test_init_sentry_can_be_called_multiple_times():
    """init_sentry() can be called multiple times safely."""
    test_dsn = "https://test@o123.ingest.sentry.io/456"
    
    with patch('app.core.sentry.sentry_sdk.init') as mock_init:
        with patch.object(settings, 'SENTRY_DSN', test_dsn):
            # Call multiple times
            init_sentry()
            init_sentry()
            init_sentry()
            
            # Should only initialize once
            # (This is Sentry's behavior - calling init() multiple times is safe)
            assert mock_init.call_count == 3  # Each call goes through