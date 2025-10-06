"""
Auth Test Helper - Workstream C
Helper functions to load and use auth fixtures in tests
"""

import json
from pathlib import Path

# Load auth fixtures
FIXTURES_PATH = Path(__file__).parent / "fixtures" / "auth_fixtures.json"

def load_auth_fixtures():
    """Load auth fixtures from JSON file"""
    with open(FIXTURES_PATH) as f:
        return json.load(f)

def get_auth_header(user_type: str = "test_admin"):
    """
    Get authorization header for test user
    
    Args:
        user_type: One of test_admin, test_provider, test_student, test_readonly
    
    Returns:
        dict with Authorization header
    """
    fixtures = load_auth_fixtures()
    token = fixtures[user_type]["token"]
    return {"Authorization": f"Bearer {token}"}

def get_token(user_type: str = "test_admin"):
    """Get raw token for test user"""
    fixtures = load_auth_fixtures()
    return fixtures[user_type]["token"]

def get_user_info(user_type: str = "test_admin"):
    """Get full user info from fixtures"""
    fixtures = load_auth_fixtures()
    return fixtures[user_type]

# Pre-defined headers for common test scenarios
ADMIN_HEADERS = get_auth_header("test_admin")
PROVIDER_HEADERS = get_auth_header("test_provider")
STUDENT_HEADERS = get_auth_header("test_student")
READONLY_HEADERS = get_auth_header("test_readonly")
