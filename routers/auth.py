"""
Authentication Router
Handles user authentication and token management
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from middleware.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    User,
    authenticate_user,
    create_access_token,
    optional_auth,
    require_auth,
)
from utils.logger import get_logger

logger = get_logger("auth")
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    roles: list[str]
    scopes: list[str]
    is_active: bool

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token"""
    from observability.metrics import metrics_service
    
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        metrics_service.record_auth_request("/api/v1/auth/login", "failure", 401)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.user_id,
            "roles": user.roles,
            "scopes": user.scopes
        },
        expires_delta=access_token_expires
    )

    logger.info(f"Successful login for user: {user.user_id}")
    metrics_service.record_auth_request("/api/v1/auth/login", "success", 200)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login-simple", response_model=Token)
async def login_simple(login_data: LoginRequest):
    """Simple login endpoint for JSON requests"""
    from observability.metrics import metrics_service
    
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {login_data.username}")
        metrics_service.record_auth_request("/api/v1/auth/login-simple", "failure", 401)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.user_id,
            "roles": user.roles,
            "scopes": user.scopes
        },
        expires_delta=access_token_expires
    )

    logger.info(f"Successful login for user: {user.user_id}")
    metrics_service.record_auth_request("/api/v1/auth/login-simple", "success", 200)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth())):
    """Get current user information"""
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        roles=current_user.roles,
        scopes=current_user.scopes,
        is_active=current_user.is_active
    )

@router.post("/logout")
async def logout(current_user: User = Depends(require_auth())):
    """Logout user (client should discard token)"""
    logger.info(f"User logged out: {current_user.user_id}")
    return {"message": "Successfully logged out"}

@router.get("/check")
async def check_auth(current_user: User | None = Depends(optional_auth)):
    """Check authentication status"""
    if current_user:
        return {
            "authenticated": True,
            "user_id": current_user.user_id,
            "roles": current_user.roles
        }
    return {"authenticated": False}
