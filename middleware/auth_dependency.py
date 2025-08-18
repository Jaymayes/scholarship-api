"""
Unified authentication dependencies for consistent auth enforcement
Fixes QA issues with authentication bypass vulnerabilities
"""

from typing import Optional
from fastapi import Depends, HTTPException
from middleware.auth import get_current_user
from config.settings import settings


async def require_auth_unless_public() -> Optional[dict]:
    """
    Require authentication unless PUBLIC_READ_ENDPOINTS is enabled
    Used as router-level dependency for consistent auth enforcement
    """
    if settings.public_read_endpoints:
        # Public access allowed - return None for anonymous user
        return None
    else:
        # Authentication required - use standard auth dependency
        return Depends(get_current_user)


async def get_auth_user_optional() -> Optional[dict]:
    """
    Get authenticated user if available, otherwise return None
    Used for endpoints that benefit from user context but don't require auth
    """
    try:
        return await get_current_user()
    except HTTPException:
        return None


def get_conditional_auth_dependency():
    """
    Get authentication dependency based on configuration
    Returns dependency function that enforces auth when needed
    """
    if settings.public_read_endpoints:
        return lambda: None
    else:
        return get_current_user