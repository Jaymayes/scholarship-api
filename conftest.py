"""
Global pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with appropriate settings"""
    # Store original env vars
    original_vars = {}
    test_vars = {
        'ENVIRONMENT': 'development',
        'DISABLE_RATE_LIMIT_BACKEND': 'true',
        'RATE_LIMIT_ENABLED': 'false',
        'PUBLIC_READ_ENDPOINTS': 'true',
        'DEBUG': 'true',
        'JWT_SECRET_KEY': 'test-secret-key-at-least-32-chars-long-for-testing-purposes',
        'ALLOWED_HOSTS': '',
        'TRUSTED_PROXY_IPS': '',
        'CORS_ALLOWED_ORIGINS': ''
    }
    
    # Save originals and set test values
    for key, value in test_vars.items():
        if key in os.environ:
            original_vars[key] = os.environ[key]
        os.environ[key] = value
    
    # Clear settings cache if it exists
    from config.settings import get_settings
    if hasattr(get_settings, 'cache_clear'):
        get_settings.cache_clear()
    
    yield
    
    # Restore original values
    for key, value in test_vars.items():
        if key in original_vars:
            os.environ[key] = original_vars[key]
        elif key in os.environ:
            del os.environ[key]

@pytest.fixture
def test_client():
    """Get test client with proper configuration"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)