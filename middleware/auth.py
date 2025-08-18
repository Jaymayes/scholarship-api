"""
Authentication and Authorization Middleware
Implementation of JWT-based authentication with role-based access control
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os

# Configuration - import from settings for secure JWT handling
from config.settings import settings

# JWT Configuration with rotation support
def get_jwt_secret_key() -> str:
    """Get JWT secret key securely"""
    return settings.get_jwt_secret_key

def get_jwt_algorithm() -> str:
    """Get JWT algorithm"""
    return settings.jwt_algorithm

def get_jwt_previous_keys() -> List[str]:
    """Get previous JWT keys for token rotation"""
    return settings.get_jwt_previous_keys

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    roles: List[str] = []
    scopes: List[str] = []

class User(BaseModel):
    user_id: str
    email: str
    roles: List[str] = []
    scopes: List[str] = []
    is_active: bool = True

# Mock user database (replace with real database in production)
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

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password"""
    user_data = MOCK_USERS.get(username)
    if not user_data:
        return None
    
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    return User(**user_data)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # Always use the current JWT secret for signing new tokens
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret_key(), algorithm=get_jwt_algorithm())
    return encoded_jwt

def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token with rotation support"""
    # Try current key first
    keys_to_try = [get_jwt_secret_key()] + get_jwt_previous_keys()
    
    for secret_key in keys_to_try:
        try:
            payload = jwt.decode(token, secret_key, algorithms=[get_jwt_algorithm()])
            user_id: str = payload.get("sub")
            roles: List[str] = payload.get("roles", [])
            scopes: List[str] = payload.get("scopes", [])
            
            if user_id is None:
                continue
                
            return TokenData(user_id=user_id, roles=roles, scopes=scopes)
        except JWTError:
            continue
    
    return None

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get the current authenticated user from JWT token"""
    if not credentials:
        return None
    
    token_data = decode_token(credentials.credentials)
    if not token_data:
        return None
    
    # Get user from mock database
    user_data = MOCK_USERS.get(token_data.user_id)
    if not user_data:
        return None
    
    return User(**user_data)

def require_auth(min_role: str = "user", scopes: Optional[List[str]] = None):
    """Require authentication with optional role and scope requirements"""
    def auth_dependency(user: Optional[User] = Depends(get_current_user)) -> User:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Check role requirements
        role_hierarchy = {"user": 0, "partner": 1, "admin": 2}
        user_level = max([role_hierarchy.get(role, -1) for role in user.roles])
        required_level = role_hierarchy.get(min_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {min_role} or higher"
            )
        
        # Check scope requirements
        if scopes:
            for scope in scopes:
                if scope not in user.scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required scope: {scope}"
                    )
        
        return user
    
    return auth_dependency

def require_admin():
    """Require admin role"""
    return require_auth(min_role="admin")

def require_scopes(required_scopes: List[str]):
    """Require specific scopes for endpoint access"""
    def scope_checker(user: User = Depends(require_auth)) -> User:
        for scope in required_scopes:
            if scope not in user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required scope: {scope}"
                )
        return user
    return scope_checker

def require_roles(required_roles: List[str]):
    """Require specific roles for endpoint access"""
    def role_checker(user: User = Depends(require_auth)) -> User:
        user_has_required_role = any(role in user.roles for role in required_roles)
        if not user_has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return user
    return role_checker

# Public access (no authentication required)
def optional_auth(user: Optional[User] = Depends(get_current_user)) -> Optional[User]:
    """Optional authentication - returns user if authenticated, None otherwise"""
    return user

def get_user_context(request: Request) -> Dict[str, Any]:
    """Extract user context from request for logging"""
    # This would be set by middleware that processes JWT tokens
    return getattr(request.state, "user_context", {})