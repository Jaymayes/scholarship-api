"""
Auth Seeding Script - Workstream C
CEO Directive: 100% Readiness - Get test suite to 13/13 green

Creates deterministic test users and JWT tokens for testing.
This script is ONLY for test/development environments.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jose import jwt
from passlib.context import CryptContext

from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestAuthSeeder:
    """Deterministic auth seeding for test environments"""
    
    def __init__(self):
        self.test_users = self._create_test_users()
        self.jwt_fixtures = {}
    
    def _create_test_users(self) -> dict:
        """Create deterministic test users"""
        return {
            "test_admin": {
                "user_id": "test_admin",
                "email": "test_admin@test.com",
                "password": "Test123!Admin",
                "hashed_password": pwd_context.hash("Test123!Admin"),
                "roles": ["admin"],
                "scopes": [
                    "scholarships:read",
                    "scholarships:write",
                    "analytics:read",
                    "analytics:write",
                    "users:admin"
                ],
                "is_active": True
            },
            "test_provider": {
                "user_id": "test_provider",
                "email": "test_provider@test.com",
                "password": "Test123!Provider",
                "hashed_password": pwd_context.hash("Test123!Provider"),
                "roles": ["partner"],
                "scopes": [
                    "scholarships:read",
                    "scholarships:write",
                    "analytics:read"
                ],
                "is_active": True
            },
            "test_student": {
                "user_id": "test_student",
                "email": "test_student@test.com",
                "password": "Test123!Student",
                "hashed_password": pwd_context.hash("Test123!Student"),
                "roles": ["user"],
                "scopes": [
                    "scholarships:read"
                ],
                "is_active": True
            },
            "test_readonly": {
                "user_id": "test_readonly",
                "email": "test_readonly@test.com",
                "password": "Test123!Readonly",
                "hashed_password": pwd_context.hash("Test123!Readonly"),
                "roles": ["read-only"],
                "scopes": [
                    "scholarships:read"
                ],
                "is_active": True
            },
            "test_inactive": {
                "user_id": "test_inactive",
                "email": "test_inactive@test.com",
                "password": "Test123!Inactive",
                "hashed_password": pwd_context.hash("Test123!Inactive"),
                "roles": ["user"],
                "scopes": ["scholarships:read"],
                "is_active": False
            }
        }
    
    def generate_jwt_tokens(self) -> dict:
        """Generate JWT tokens for all test users"""
        secret_key = settings.get_jwt_secret_key
        algorithm = settings.jwt_algorithm
        
        for username, user_data in self.test_users.items():
            # Create token with 24 hour expiry for tests
            now = datetime.utcnow()
            expire = now + timedelta(hours=24)
            
            payload = {
                "sub": user_data["user_id"],
                "exp": int(expire.timestamp()),
                "iat": int(now.timestamp()),
                "roles": user_data["roles"],
                "scopes": user_data["scopes"]
            }
            
            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            
            self.jwt_fixtures[username] = {
                "username": username,
                "password": user_data["password"],
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "roles": user_data["roles"],
                "scopes": user_data["scopes"],
                "is_active": user_data["is_active"],
                "token": token,
                "token_type": "bearer",
                "expires_at": expire.isoformat()
            }
        
        return self.jwt_fixtures
    
    def save_fixtures(self, output_path: str = "tests/fixtures/auth_fixtures.json"):
        """Save JWT fixtures to JSON file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(self.jwt_fixtures, f, indent=2)
        
        print(f"✅ Auth fixtures saved to: {output_path}")
    
    def update_mock_users(self):
        """Update middleware/auth.py with test users (development only)"""
        if settings.environment.value not in ["development", "local"]:
            print("❌ Cannot update mock users in production environment")
            return
        
        auth_file = Path("middleware/auth.py")
        content = auth_file.read_text()
        
        # Build MOCK_USERS dict
        mock_users_code = "MOCK_USERS: dict = {}\n\n"
        mock_users_code += f"# Development-only mock users (strictly controlled by environment)\n"
        mock_users_code += f"if settings.environment == settings.environment.DEVELOPMENT:\n"
        mock_users_code += "    MOCK_USERS = {\n"
        
        for username, user_data in self.test_users.items():
            mock_users_code += f'        "{username}": {{\n'
            mock_users_code += f'            "user_id": "{user_data["user_id"]}",\n'
            mock_users_code += f'            "email": "{user_data["email"]}",\n'
            mock_users_code += f'            "hashed_password": "{user_data["hashed_password"]}",\n'
            mock_users_code += f'            "roles": {user_data["roles"]},\n'
            mock_users_code += f'            "scopes": {user_data["scopes"]},\n'
            mock_users_code += f'            "is_active": {str(user_data["is_active"])}\n'
            mock_users_code += "        },\n"
        
        mock_users_code += "    }\n"
        
        # Replace MOCK_USERS section
        import re
        pattern = r'MOCK_USERS: dict = \{\}.*?(?=\ndef )'
        content = re.sub(pattern, mock_users_code, content, flags=re.DOTALL)
        
        auth_file.write_text(content)
        print("✅ Mock users updated in middleware/auth.py")
    
    def print_summary(self):
        """Print summary of seeded users"""
        print("\n" + "="*60)
        print("TEST AUTH SEEDING SUMMARY")
        print("="*60)
        
        for username, fixture in self.jwt_fixtures.items():
            print(f"\n{username}:")
            print(f"  User ID: {fixture['user_id']}")
            print(f"  Email: {fixture['email']}")
            print(f"  Password: {fixture['password']}")
            print(f"  Roles: {', '.join(fixture['roles'])}")
            print(f"  Scopes: {', '.join(fixture['scopes'])}")
            print(f"  Active: {fixture['is_active']}")
            print(f"  Token (first 50): {fixture['token'][:50]}...")
        
        print("\n" + "="*60)
        print("USAGE IN TESTS:")
        print("="*60)
        print("""
# Load fixtures in your tests:
import json

with open('tests/fixtures/auth_fixtures.json') as f:
    auth_fixtures = json.load(f)

# Use in test requests:
admin_token = auth_fixtures['test_admin']['token']
headers = {
    'Authorization': f'Bearer {admin_token}'
}

response = client.get('/api/v1/scholarships', headers=headers)
""")
    
    def create_test_helper(self):
        """Create helper module for tests"""
        helper_code = '''"""
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
'''
        
        helper_path = Path("tests/auth_helper.py")
        helper_path.write_text(helper_code)
        print(f"✅ Test helper created at: {helper_path}")


def main(fixture_only: bool = False):
    """
    Main seeding function
    
    Args:
        fixture_only: If True, only generate fixtures without modifying middleware
    """
    print("🌱 Starting test auth seeding...")
    
    # Security guard: Check for explicit test seeding authorization
    allow_test_seeding = os.getenv("ALLOW_TEST_SEEDING", "0") == "1"
    is_safe_env = settings.environment.value in ["development", "test", "local"]
    
    # Production protection
    if settings.environment.value == "production" and not allow_test_seeding:
        print("❌ ERROR: Cannot seed test users in production!")
        print("   Set ALLOW_TEST_SEEDING=1 only if you understand the security implications.")
        sys.exit(1)
    
    # Create seeder
    seeder = TestAuthSeeder()
    
    # Generate JWT tokens
    print("🔑 Generating JWT tokens...")
    seeder.generate_jwt_tokens()
    
    # Save fixtures (ALWAYS safe - just creates JSON file)
    print("💾 Saving fixtures...")
    seeder.save_fixtures()
    
    # Create test helper (ALWAYS safe - just creates helper module)
    print("🛠️  Creating test helper...")
    seeder.create_test_helper()
    
    # Update mock users ONLY in development (modifies code)
    if not fixture_only and is_safe_env:
        print("🔄 Updating mock users...")
        seeder.update_mock_users()
    elif not is_safe_env:
        print(f"⚠️  Skipping mock user update (environment={settings.environment.value})")
        print("   Fixtures generated for test consumption only.")
    
    # Print summary
    seeder.print_summary()
    
    print("\n✅ Test auth seeding complete!")
    print("\nNext steps:")
    if is_safe_env and not fixture_only:
        print("1. Restart the application to load new mock users")
        print("2. Run tests with: pytest tests/ -v")
    else:
        print("1. Tests will use fixtures from tests/fixtures/auth_fixtures.json")
        print("2. Run tests with: pytest tests/ -v")
    print("3. Check auth_fixtures.json for credentials")


if __name__ == "__main__":
    # Check if running in fixture-only mode
    fixture_only = len(sys.argv) > 1 and sys.argv[1] == "--fixture-only"
    main(fixture_only=fixture_only)
