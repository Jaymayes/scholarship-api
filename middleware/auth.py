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

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        scopes: List[str] = payload.get("scopes", [])
        
        if user_id is None:
            return None
            
        return TokenData(user_id=user_id, roles=roles, scopes=scopes)
    except JWTError:
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

def require_auth(request: Request, user: Optional[User] = Depends(get_current_user)) -> User:
    """Require authentication for protected endpoints"""
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
    
    return user

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