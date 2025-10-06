"""
Global pytest configuration and fixtures
"""
import os

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with appropriate settings"""
    # Store original env vars
    original_vars = {}
    test_vars = {
        'ENVIRONMENT': 'development',
        'STRICT_CONFIG_VALIDATION': 'false',
        'DISABLE_RATE_LIMIT_BACKEND': 'true',
        'RATE_LIMIT_ENABLED': 'false',
        'PUBLIC_READ_ENDPOINTS': 'true',
        'DEBUG': 'true',
        'JWT_SECRET_KEY': 'test-secret-key-for-testing-must-be-at-least-64-characters-long-to-pass-production-validation-checks',
        'ALLOWED_HOSTS': '["localhost","127.0.0.1","testserver"]',
        'TRUSTED_PROXY_IPS': '[]',
        'CORS_ALLOWED_ORIGINS': '*'
    }

    # Save originals and set test values
    for key, value in test_vars.items():
        if key in os.environ:
            original_vars[key] = os.environ[key]
        os.environ[key] = value

    # Clear settings cache if it exists
    try:
        from config.settings import get_settings
        if callable(getattr(get_settings, 'cache_clear', None)):
            get_settings.cache_clear()
        
        # Force reload of settings module to pick up new env vars
        import config.settings
        import importlib
        importlib.reload(config.settings)
    except Exception as e:
        print(f"Warning: Could not reload settings: {e}")

    yield

    # Restore original values
    for key, value in test_vars.items():
        if key in original_vars:
            os.environ[key] = original_vars[key]
        elif key in os.environ:
            del os.environ[key]

@pytest.fixture
def test_client():
    """Get test client with proper configuration and test user fixtures"""
    from fastapi.testclient import TestClient
    
    # Load test auth fixtures and populate MOCK_USERS for tests
    import json
    from pathlib import Path
    from middleware.auth import MOCK_USERS, pwd_context
    
    fixtures_path = Path(__file__).parent / "tests" / "fixtures" / "auth_fixtures.json"
    if fixtures_path.exists():
        with open(fixtures_path) as f:
            auth_fixtures = json.load(f)
        
        # Populate MOCK_USERS with test fixtures
        for username, fixture in auth_fixtures.items():
            MOCK_USERS[username] = {
                "user_id": fixture["user_id"],
                "email": fixture["email"],
                "hashed_password": pwd_context.hash(fixture["password"]),
                "roles": fixture["roles"],
                "scopes": fixture["scopes"],
                "is_active": fixture["is_active"]
            }

    from main import app
    return TestClient(app)
