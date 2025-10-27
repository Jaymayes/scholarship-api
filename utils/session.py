"""Session ID extraction utilities for business event tracking"""
from typing import Optional
from fastapi import Request


def extract_session_id(request: Request) -> Optional[str]:
    """
    Extract session ID from request headers for user journey tracking.
    
    Priority order:
    1. X-Session-ID header (explicit session tracking)
    2. Session cookie
    3. None if not available
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Session ID string or None
    """
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return session_id
    
    if hasattr(request.state, "session_id"):
        return request.state.session_id
    
    session_cookie = request.cookies.get("session_id")
    if session_cookie:
        return session_cookie
    
    return None


def extract_actor_id(request: Request) -> Optional[str]:
    """
    Extract actor (user) ID from request.
    
    Priority order:
    1. Authenticated user ID from request.state.user_id
    2. X-User-ID header
    3. None for anonymous requests
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User ID string or None
    """
    if hasattr(request.state, "user_id"):
        return request.state.user_id
    
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return user_id
    
    return None
