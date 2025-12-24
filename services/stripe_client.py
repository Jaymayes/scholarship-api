"""
Stripe Client Service
Fetches Stripe credentials from Replit Connector API
"""

import os
import logging
from typing import Optional, Tuple
import httpx
import stripe

logger = logging.getLogger(__name__)

_cached_credentials: Optional[dict] = None


class StripeConfigurationError(Exception):
    """Raised when Stripe credentials cannot be obtained"""
    pass


async def get_stripe_credentials() -> Tuple[str, str]:
    """
    Fetch Stripe credentials from environment variables or Replit Connector API
    
    Priority: Environment variables > Connector API
    This ensures Python FastAPI apps work without requiring the JS-only connector.
    
    Returns:
        Tuple of (publishable_key, secret_key)
    
    Raises:
        StripeConfigurationError: If credentials cannot be fetched
    """
    global _cached_credentials
    
    if _cached_credentials:
        return _cached_credentials["publishable"], _cached_credentials["secret"]
    
    secret_key = os.environ.get("STRIPE_SECRET_KEY")
    publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    
    if secret_key:
        logger.info("Using STRIPE_SECRET_KEY from environment variables (preferred for Python apps)")
        _cached_credentials = {
            "publishable": publishable_key or "",
            "secret": secret_key
        }
        return publishable_key or "", secret_key
    
    hostname = os.environ.get("REPLIT_CONNECTORS_HOSTNAME")
    
    if not hostname:
        logger.error("No STRIPE_SECRET_KEY and no connector hostname available")
        raise StripeConfigurationError(
            "Stripe not configured. Set STRIPE_SECRET_KEY or configure Stripe integration."
        )
    
    repl_identity = os.environ.get("REPL_IDENTITY")
    web_repl_renewal = os.environ.get("WEB_REPL_RENEWAL")
    
    if repl_identity:
        x_replit_token = f"repl {repl_identity}"
    elif web_repl_renewal:
        x_replit_token = f"depl {web_repl_renewal}"
    else:
        raise StripeConfigurationError(
            "Replit identity token not found. Please run in Replit environment."
        )
    
    is_production = os.environ.get("REPLIT_DEPLOYMENT") == "1"
    target_environment = "production" if is_production else "development"
    
    url = f"https://{hostname}/api/v2/connection"
    params = {
        "include_secrets": "true",
        "connector_names": "stripe",
        "environment": target_environment
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            headers={
                "Accept": "application/json",
                "X_REPLIT_TOKEN": x_replit_token
            },
            timeout=10.0
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch Stripe credentials: {response.status_code}")
            raise RuntimeError(f"Failed to fetch Stripe credentials: HTTP {response.status_code}")
        
        data = response.json()
        
    connection = data.get("items", [{}])[0] if data.get("items") else {}
    settings = connection.get("settings", {})
    
    publishable = settings.get("publishable")
    secret = settings.get("secret")
    
    if not publishable or not secret:
        env_secret = os.environ.get("STRIPE_SECRET_KEY")
        env_publishable = os.environ.get("STRIPE_PUBLISHABLE_KEY")
        
        if env_secret:
            logger.info("Connector returned incomplete data, using STRIPE_SECRET_KEY from environment")
            _cached_credentials = {
                "publishable": env_publishable or "",
                "secret": env_secret
            }
            return env_publishable or "", env_secret
        
        raise StripeConfigurationError(
            f"Stripe {target_environment} connection not found or incomplete. "
            "Please configure the Stripe integration in Replit."
        )
    
    _cached_credentials = {
        "publishable": publishable,
        "secret": secret
    }
    
    logger.info(f"Stripe credentials loaded for {target_environment} environment")
    return publishable, secret


async def get_stripe_secret_key() -> str:
    """Get just the secret key"""
    _, secret = await get_stripe_credentials()
    return secret


async def get_publishable_key() -> str:
    """Get the Stripe publishable key for frontend"""
    publishable, _ = await get_stripe_credentials()
    return publishable


async def configure_stripe() -> None:
    """
    Configure the global stripe module with the secret key
    This is the pattern for stripe v13.x
    """
    secret_key = await get_stripe_secret_key()
    stripe.api_key = secret_key


def clear_credentials_cache():
    """Clear cached credentials (for testing or credential rotation)"""
    global _cached_credentials
    _cached_credentials = None
    stripe.api_key = None
