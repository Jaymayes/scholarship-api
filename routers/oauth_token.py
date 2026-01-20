"""
OAuth 2.0 Token Endpoint
Phase 2 Auth/OIDC Repair: RFC 6749 compliant token endpoint with input validation

Implements:
- /oauth/token endpoint
- /token endpoint (alias)
- RFC 6749 error responses with error_description
- client_id validation
- grant_type validation (allowed set)
"""

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

from middleware.auth import create_access_token, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["OAuth2"])

ALLOWED_GRANT_TYPES = {
    "password",
    "client_credentials", 
    "authorization_code",
    "refresh_token"
}


class OAuth2ErrorResponse(BaseModel):
    """RFC 6749 Section 5.2 Error Response"""
    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None


class TokenResponse(BaseModel):
    """RFC 6749 Section 5.1 Successful Response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: Optional[str] = None
    refresh_token: Optional[str] = None


def oauth2_error(error: str, description: str, status_code: int = 400) -> JSONResponse:
    """
    Return RFC 6749 compliant error response.
    
    Error codes per RFC 6749 Section 5.2:
    - invalid_request: Missing required parameter or invalid request
    - invalid_client: Client authentication failed
    - invalid_grant: Invalid authorization grant or refresh token
    - unauthorized_client: Client not authorized for this grant type
    - unsupported_grant_type: Grant type not supported
    - invalid_scope: Requested scope is invalid or exceeds granted scope
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "error_description": description
        },
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache"
        }
    )


@router.post("/oauth/token", response_model=TokenResponse)
async def oauth_token(
    request: Request,
    grant_type: str = Form(None),
    client_id: str = Form(None),
    client_secret: str = Form(None),
    username: str = Form(None),
    password: str = Form(None),
    scope: str = Form(None),
    code: str = Form(None),
    redirect_uri: str = Form(None),
    refresh_token: str = Form(None)
):
    """
    OAuth 2.0 Token Endpoint (RFC 6749 Section 3.2)
    
    Supports:
    - password grant (username + password)
    - client_credentials grant (client_id + client_secret)
    - authorization_code grant (code + redirect_uri)
    - refresh_token grant (refresh_token)
    
    Returns RFC 6749 compliant error responses for validation failures.
    """
    from observability.metrics import metrics_service
    
    if not client_id:
        logger.warning("OAuth token request missing client_id")
        metrics_service.record_auth_request("/oauth/token", "failure", 400)
        return oauth2_error(
            "invalid_request",
            "The 'client_id' parameter is required."
        )
    
    if not grant_type:
        logger.warning(f"OAuth token request missing grant_type (client_id={client_id})")
        metrics_service.record_auth_request("/oauth/token", "failure", 400)
        return oauth2_error(
            "invalid_request",
            "The 'grant_type' parameter is required."
        )
    
    if grant_type not in ALLOWED_GRANT_TYPES:
        logger.warning(f"OAuth unsupported grant_type: {grant_type} (client_id={client_id})")
        metrics_service.record_auth_request("/oauth/token", "failure", 400)
        return oauth2_error(
            "unsupported_grant_type",
            f"The grant type '{grant_type}' is not supported. Allowed: {', '.join(sorted(ALLOWED_GRANT_TYPES))}"
        )
    
    if grant_type == "password":
        if not username or not password:
            logger.warning(f"Password grant missing credentials (client_id={client_id})")
            metrics_service.record_auth_request("/oauth/token", "failure", 400)
            return oauth2_error(
                "invalid_request",
                "The 'username' and 'password' parameters are required for password grant."
            )
        
        user = authenticate_user(username, password)
        if not user:
            logger.warning(f"OAuth password grant failed for username: {username}")
            metrics_service.record_auth_request("/oauth/token", "failure", 401)
            return oauth2_error(
                "invalid_grant",
                "The provided username or password is incorrect.",
                status_code=401
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.user_id,
                "roles": user.roles,
                "scopes": user.scopes,
                "client_id": client_id
            },
            expires_delta=access_token_expires
        )
        
        logger.info(f"OAuth password grant successful for user: {user.user_id}")
        metrics_service.record_auth_request("/oauth/token", "success", 200)
        
        return JSONResponse(
            status_code=200,
            content={
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "scope": " ".join(user.scopes) if user.scopes else None
            },
            headers={
                "Cache-Control": "no-store",
                "Pragma": "no-cache"
            }
        )
    
    elif grant_type == "client_credentials":
        if not client_secret:
            logger.warning(f"Client credentials grant missing client_secret (client_id={client_id})")
            metrics_service.record_auth_request("/oauth/token", "failure", 400)
            return oauth2_error(
                "invalid_request",
                "The 'client_secret' parameter is required for client_credentials grant."
            )
        
        if client_id == "scholarship_api_service" and client_secret == settings.external_billing_api_key:
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={
                    "sub": client_id,
                    "roles": ["service"],
                    "scopes": ["api:read", "api:write"],
                    "client_id": client_id
                },
                expires_delta=access_token_expires
            )
            
            logger.info(f"OAuth client_credentials grant successful for: {client_id}")
            metrics_service.record_auth_request("/oauth/token", "success", 200)
            
            return JSONResponse(
                status_code=200,
                content={
                    "access_token": access_token,
                    "token_type": "Bearer",
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    "scope": "api:read api:write"
                },
                headers={
                    "Cache-Control": "no-store",
                    "Pragma": "no-cache"
                }
            )
        else:
            logger.warning(f"OAuth client_credentials grant failed - invalid credentials (client_id={client_id})")
            metrics_service.record_auth_request("/oauth/token", "failure", 401)
            return oauth2_error(
                "invalid_client",
                "Client authentication failed.",
                status_code=401
            )
    
    elif grant_type == "authorization_code":
        if not code:
            logger.warning(f"Authorization code grant missing code (client_id={client_id})")
            metrics_service.record_auth_request("/oauth/token", "failure", 400)
            return oauth2_error(
                "invalid_request",
                "The 'code' parameter is required for authorization_code grant."
            )
        
        logger.warning(f"Authorization code grant not implemented (client_id={client_id})")
        metrics_service.record_auth_request("/oauth/token", "failure", 400)
        return oauth2_error(
            "invalid_grant",
            "Authorization code grant not yet implemented. Use password or client_credentials grant."
        )
    
    elif grant_type == "refresh_token":
        if not refresh_token:
            logger.warning(f"Refresh token grant missing refresh_token (client_id={client_id})")
            metrics_service.record_auth_request("/oauth/token", "failure", 400)
            return oauth2_error(
                "invalid_request",
                "The 'refresh_token' parameter is required for refresh_token grant."
            )
        
        logger.warning(f"Refresh token grant not implemented (client_id={client_id})")
        metrics_service.record_auth_request("/oauth/token", "failure", 400)
        return oauth2_error(
            "invalid_grant",
            "Refresh token grant not yet implemented."
        )
    
    return oauth2_error(
        "server_error",
        "An unexpected error occurred.",
        status_code=500
    )


@router.post("/token", response_model=TokenResponse)
async def token_alias(
    request: Request,
    grant_type: str = Form(None),
    client_id: str = Form(None),
    client_secret: str = Form(None),
    username: str = Form(None),
    password: str = Form(None),
    scope: str = Form(None),
    code: str = Form(None),
    redirect_uri: str = Form(None),
    refresh_token: str = Form(None)
):
    """
    Token Endpoint Alias (/token)
    
    Alias for /oauth/token for compatibility with OAuth2 clients that expect /token.
    """
    return await oauth_token(
        request=request,
        grant_type=grant_type,
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        scope=scope,
        code=code,
        redirect_uri=redirect_uri,
        refresh_token=refresh_token
    )
