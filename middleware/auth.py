"""
Authentication and Authorization Middleware
Implementation of JWT-based authentication with role-based access control
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# Configuration - import from settings for secure JWT handling
from config.settings import settings
from middleware.error_handling import APIError


# JWT Configuration with rotation support
def get_jwt_secret_key() -> str:
    """Get JWT secret key securely"""
    return settings.get_jwt_secret_key

def get_jwt_algorithm() -> str:
    """Get JWT algorithm"""
    return settings.jwt_algorithm

def get_jwt_previous_keys() -> list[str]:
    """Get previous JWT keys for token rotation"""
    return settings.get_jwt_previous_keys

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)  # Let custom auth logic handle errors properly

class Token(BaseModel):
    access_token: str
    token_type: str

class JWTPayload(BaseModel):
    """JWT payload structure"""
    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    roles: list[str] = Field(default=[], description="User roles")
    scopes: list[str] = Field(default=[], description="User scopes")
    iat: int | None = Field(None, description="Issued at timestamp")
    iss: str | None = Field(None, description="Issuer")
    aud: str | None = Field(None, description="Audience")

class TokenData(BaseModel):
    user_id: str = Field(..., description="User identifier")
    roles: list[str] = Field(default=[], description="User roles")
    scopes: list[str] = Field(default=[], description="User scopes")

class User(BaseModel):
    user_id: str
    email: str
    roles: list[str] = []
    scopes: list[str] = []
    is_active: bool = True

# DAY 0 CEO DIRECTIVE: MOCK_USERS REMOVED FROM PRODUCTION
# Security risk: hardcoded credentials with weak passwords
# Production must use database-backed authentication only
MOCK_USERS: dict = {}

# Development-only mock users (strictly controlled by environment)
if settings.environment == settings.environment.DEVELOPMENT:
    MOCK_USERS = {
        "admin": {
            "user_id": "admin",
            "email": "admin@scholarship-api.com",
            "hashed_password": pwd_context.hash("admin123"),
            "roles": ["admin"],
            "scopes": ["scholarships:read", "scholarships:write", "analytics:read", "analytics:write"],
            "is_active": True
        },
        "partner": {
            "user_id": "partner",
            "email": "partner@university.edu",
            "hashed_password": pwd_context.hash("partner123"),
            "roles": ["partner"],
            "scopes": ["scholarships:read", "scholarships:write", "analytics:read"],
            "is_active": True
        },
        "readonly": {
            "user_id": "readonly",
            "email": "readonly@client.com",
            "hashed_password": pwd_context.hash("readonly123"),
            "roles": ["read-only"],
            "scopes": ["scholarships:read"],
            "is_active": True
        }
    }

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user by username and password"""
    user_data = MOCK_USERS.get(username)
    if not user_data:
        return None

    if not verify_password(password, user_data["hashed_password"]):
        return None

    return User(**user_data)

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token with properly typed payload"""
    from observability.metrics import metrics_service
    
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Create base payload
    payload_dict = {
        "sub": str(data["sub"]),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "roles": data.get("roles", []),
        "scopes": data.get("scopes", [])
    }
    
    # Add issuer and audience if configured (required for validation)
    if hasattr(settings, 'jwt_issuer') and settings.jwt_issuer:
        payload_dict["iss"] = settings.jwt_issuer
    if hasattr(settings, 'jwt_audience') and settings.jwt_audience:
        payload_dict["aud"] = settings.jwt_audience
    
    # Create typed payload
    payload = JWTPayload(**payload_dict)

    # Always use the current JWT secret for signing new tokens
    encoded_jwt = jwt.encode(payload.model_dump(exclude_none=True), get_jwt_secret_key(), algorithm=get_jwt_algorithm())
    
    # Record token creation metric
    metrics_service.record_token_operation("create", "success")
    
    return encoded_jwt

async def decode_token(token: str) -> TokenData | None:
    """
    Decode and validate JWT with hardened security
    
    Supports both:
    - RS256 tokens from scholar_auth (via JWKS)
    - HS256 tokens (legacy, for backward compatibility)
    
    CEO Directive: RS256 JWKS validation with clock skew tolerance
    """
    from observability.metrics import metrics_service
    from services.jwks_client import verify_rs256_token
    
    if not token or not isinstance(token, str) or len(token.strip()) == 0:
        metrics_service.record_token_operation("validate", "failure")
        return None

    # Security: Reject tokens with 'none' algorithm
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get('alg', '').upper()
        
        if alg in ['NONE', 'NULL', '']:
            return None
        
        # RS256 token from scholar_auth - validate with JWKS
        if alg == 'RS256':
            try:
                payload = await verify_rs256_token(token)
                if payload:
                    user_id = payload.get("sub")
                    roles = payload.get("roles", [])
                    scopes = payload.get("scopes", [])
                    
                    # Ensure valid types
                    if not user_id or not isinstance(user_id, str):
                        return None
                    if not isinstance(roles, list):
                        roles = []
                    if not isinstance(scopes, list):
                        scopes = []
                    
                    metrics_service.record_token_operation("validate", "success")
                    return TokenData(user_id=user_id, roles=roles, scopes=scopes)
            except Exception as e:
                import logging
                logging.warning(f"RS256 validation failed: {type(e).__name__}: {e}")
        
        # HS256 token (legacy) - validate with shared secret
        elif alg == 'HS256':
            keys_to_try = [get_jwt_secret_key()] + get_jwt_previous_keys()

            for secret_key in keys_to_try:
                if not secret_key or len(secret_key.strip()) < 32:
                    continue

                try:
                    # Build decode options
                    decode_options = {
                        "require_exp": True,
                        "require_iat": True,
                        "verify_exp": True,
                        "verify_iat": True,
                        "verify_signature": True
                    }
                    
                    # Build decode kwargs
                    decode_kwargs = {
                        "algorithms": ["HS256"],
                        "options": decode_options
                    }
                    
                    # Add issuer and audience validation if configured
                    if hasattr(settings, 'jwt_issuer') and settings.jwt_issuer:
                        decode_kwargs["issuer"] = settings.jwt_issuer
                    if hasattr(settings, 'jwt_audience') and settings.jwt_audience:
                        decode_kwargs["audience"] = settings.jwt_audience
                    
                    # SECURITY: Pin algorithm, require all time claims
                    payload = jwt.decode(token, secret_key, **decode_kwargs)

                    # Extract and validate required fields
                    user_id = payload.get("sub")
                    if not user_id or not isinstance(user_id, str) or len(user_id.strip()) == 0:
                        continue

                    roles = payload.get("roles", [])
                    scopes = payload.get("scopes", [])

                    # Ensure roles and scopes are valid lists
                    if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
                        roles = []
                    if not isinstance(scopes, list) or not all(isinstance(s, str) for s in scopes):
                        scopes = []

                    metrics_service.record_token_operation("validate", "success")
                    return TokenData(user_id=user_id, roles=roles, scopes=scopes)
                except (JWTError, ValueError, KeyError, TypeError) as e:
                    # Log security events
                    import logging
                    logging.warning(f"HS256 validation failed: {type(e).__name__}")
                    continue
        
    except Exception:
        pass

    # Security: Ensure proper token structure
    token_parts = token.split('.')
    if len(token_parts) != 3 or not all(part.strip() for part in token_parts):
        metrics_service.record_token_operation("validate", "failure")
        return None

    metrics_service.record_token_operation("validate", "failure")
    return None

async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> User | None:
    """Get the current authenticated user from JWT token"""
    if not credentials:
        return None

    token_data = await decode_token(credentials.credentials)
    if not token_data:
        return None

    # Get user from mock database - token_data.user_id is guaranteed to be str by TokenData model
    user_data = MOCK_USERS.get(token_data.user_id)
    if not user_data:
        return None

    return User(**user_data)

def require_auth(min_role: str = "user", scopes: list[str] | None = None):
    """Require authentication with optional role and scope requirements"""
    def auth_dependency(user: User | None = Depends(get_current_user)) -> User:
        from fastapi import HTTPException
        
        if not user:
            # Use HTTPException directly for proper FastAPI error handling
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if not user.is_active:
            raise APIError(
                message="User account is disabled",
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="AUTH_002"
            )

        # Check role requirements
        role_hierarchy = {"user": 0, "partner": 1, "admin": 2}
        user_level = max([role_hierarchy.get(role, -1) for role in user.roles])
        required_level = role_hierarchy.get(min_role, 999)

        if user_level < required_level:
            raise APIError(
                message=f"Insufficient permissions. Required role: {min_role} or higher",
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="AUTH_003"
            )

        # Check scope requirements
        if scopes:
            for scope in scopes:
                if scope not in user.scopes:
                    raise APIError(
                        message=f"Insufficient permissions. Required scope: {scope}",
                        status_code=status.HTTP_403_FORBIDDEN,
                        error_code="AUTH_004"
                    )

        return user

    return auth_dependency

def require_admin():
    """Require admin role"""
    return require_auth(min_role="admin")

def require_scopes(required_scopes: list[str]):
    """Require specific scopes for endpoint access"""
    def scope_checker(user: User = Depends(require_auth())) -> User:
        from middleware.error_handling import APIError
        for scope in required_scopes:
            if scope not in user.scopes:
                raise APIError(
                    message=f"Insufficient permissions. Required scope: {scope}",
                    status_code=status.HTTP_403_FORBIDDEN,
                    error_code="AUTH_004"
                )
        return user
    return scope_checker

def require_roles(required_roles: list[str]):
    """Require specific roles for endpoint access"""
    def role_checker(user: User = Depends(require_auth())) -> User:
        from middleware.error_handling import APIError
        user_has_required_role = any(role in user.roles for role in required_roles)
        if not user_has_required_role:
            raise APIError(
                message=f"Insufficient permissions. Required roles: {required_roles}",
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="AUTH_003"
            )
        return user
    return role_checker

# Public access (no authentication required)
def optional_auth(user: User | None = Depends(get_current_user)) -> User | None:
    """Optional authentication - returns user if authenticated, None otherwise"""
    return user

def get_user_context(request: Request) -> dict[str, Any]:
    """Extract user context from request for logging"""
    # This would be set by middleware that processes JWT tokens
    return getattr(request.state, "user_context", {})
