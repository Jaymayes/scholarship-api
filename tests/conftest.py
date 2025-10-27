# Test Configuration and Fixtures
# Provides reusable authenticated test client for performance testing

from datetime import timedelta
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from main import app
from middleware.auth import create_access_token


@pytest.fixture
def test_client():
    """Provide test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """
    Generate valid JWT token for authenticated testing
    
    Returns headers with Authorization: Bearer <token>
    """
    # Create test user data (must use existing mock user from middleware/auth.py)
    # Using the 'student' user from MOCK_USERS
    user_data = {
        "sub": "student",
        "roles": ["user"],
        "scopes": ["scholarships:read", "scholarships:write"]
    }
    
    # Generate valid JWT token
    token = create_access_token(
        data=user_data,
        expires_delta=timedelta(minutes=30)
    )
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers() -> Dict[str, str]:
    """
    Generate valid JWT token for admin testing
    
    Returns headers with Authorization: Bearer <token>
    """
    # Using the 'admin' user from MOCK_USERS
    admin_data = {
        "sub": "admin",
        "roles": ["admin"],
        "scopes": ["scholarships:read", "scholarships:write", "users:manage"]
    }
    
    token = create_access_token(
        data=admin_data,
        expires_delta=timedelta(minutes=30)
    )
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing"""
    return {
        "user_id": "test-user-789",
        "gpa": 3.8,
        "field_of_study": "Computer Science",
        "grade_level": "Undergraduate Junior",
        "citizenship": "US Citizen",
        "state": "California"
    }
