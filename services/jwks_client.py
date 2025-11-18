"""
JWKS Client Service - OAuth2/OIDC RS256 Validation
CEO Directive Nov 13: Robust JWKS validation with caching, backoff, and key rotation

Architect Specification:
- Async httpx client with exponential backoff + jitter
- ETag/Cache-Control respect
- Configurable TTL + stale-while-revalidate
- Background refresh on expiry
- Concurrency-safe with asyncio.Lock
- Startup prewarm + health checks
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, Optional

import httpx
from jose import jwk, jwt
from jose.exceptions import JWKError, JWTError

from config.settings import settings

logger = logging.getLogger(__name__)


class JWKSClient:
    """
    Async JWKS client with caching, retry logic, and stale-while-revalidate
    
    Features:
    - Exponential backoff with jitter for fault tolerance
    - ETag-based conditional requests
    - Stale-while-revalidate pattern (fresh TTL + grace period)
    - Concurrency-safe with asyncio.Lock
    - Metrics for observability
    """
    
    def __init__(self):
        self.jwks_url = settings.scholar_auth_jwks_url
        self.cache_ttl = settings.jwks_cache_ttl_seconds
        self.cache_max_age = settings.jwks_cache_max_age
        self.fetch_timeout = settings.jwks_fetch_timeout_seconds
        self.retry_max_attempts = settings.jwks_retry_max_attempts
        self.retry_backoff_base = settings.jwks_retry_backoff_base
        
        # Cache state
        self._keys: Dict[str, Any] = {}  # kid -> RSA key object
        self._cache_timestamp: float = 0
        self._etag: Optional[str] = None
        self._lock = asyncio.Lock()
        
        # Health status
        self._last_fetch_success: Optional[float] = None
        self._last_fetch_error: Optional[str] = None
        
        # HTTP client (async)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.fetch_timeout,
                follow_redirects=True
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _is_cache_fresh(self) -> bool:
        """Check if cache is within fresh TTL"""
        if not self._keys:
            return False
        age = time.time() - self._cache_timestamp
        return age < self.cache_ttl
    
    def _is_cache_stale(self) -> bool:
        """Check if cache is beyond max age (stale-while-revalidate expired)"""
        if not self._keys:
            return True
        age = time.time() - self._cache_timestamp
        return age > self.cache_max_age
    
    async def _fetch_jwks_with_retry(self) -> Optional[Dict[str, Any]]:
        """
        Fetch JWKS from endpoint with exponential backoff + jitter
        
        Returns:
            JWKS dict or None on failure
        """
        client = await self._get_client()
        
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                headers = {}
                if self._etag:
                    headers["If-None-Match"] = self._etag
                
                response = await client.get(self.jwks_url, headers=headers)
                
                # 304 Not Modified - use cached keys
                if response.status_code == 304:
                    logger.debug(f"JWKS cache valid (ETag match) | age={time.time() - self._cache_timestamp:.1f}s")
                    self._cache_timestamp = time.time()  # Refresh TTL
                    return None  # Signal to use existing cache
                
                response.raise_for_status()
                
                # Success - update ETag and cache
                self._etag = response.headers.get("ETag")
                jwks_data = response.json()
                
                logger.info(f"JWKS fetched successfully | keys={len(jwks_data.get('keys', []))} | attempt={attempt}")
                self._last_fetch_success = time.time()
                self._last_fetch_error = None
                
                return jwks_data
            
            except (httpx.HTTPError, ValueError) as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                self._last_fetch_error = error_msg
                
                if attempt < self.retry_max_attempts:
                    # Exponential backoff with jitter
                    backoff = self.retry_backoff_base * (2 ** (attempt - 1))
                    jitter = random.uniform(0, backoff * 0.1)  # 10% jitter
                    sleep_time = backoff + jitter
                    
                    logger.warning(
                        f"JWKS fetch failed (attempt {attempt}/{self.retry_max_attempts}): {error_msg} | "
                        f"retry_in={sleep_time:.2f}s"
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(
                        f"JWKS fetch failed after {self.retry_max_attempts} attempts: {error_msg}"
                    )
        
        return None
    
    async def _refresh_keys(self):
        """Refresh JWKS keys from endpoint (with lock for concurrency safety)"""
        async with self._lock:
            # Double-check cache freshness (another coroutine may have refreshed)
            if self._is_cache_fresh():
                return
            
            logger.debug(f"Refreshing JWKS keys | cache_age={time.time() - self._cache_timestamp:.1f}s")
            
            jwks_data = await self._fetch_jwks_with_retry()
            
            # If 304 Not Modified, jwks_data is None - keep existing keys
            if jwks_data is None:
                return
            
            # Parse keys
            new_keys = {}
            for key_data in jwks_data.get("keys", []):
                kid = key_data.get("kid", "unknown")
                try:
                    if not kid or kid == "unknown":
                        logger.warning("JWKS key missing 'kid' - skipping")
                        continue
                    
                    # Construct RSA key using python-jose
                    key_obj = jwk.construct(key_data)
                    new_keys[kid] = key_obj
                    
                except (JWKError, KeyError, ValueError) as e:
                    logger.error(f"Failed to construct key kid={kid}: {e}")
                    continue
            
            if new_keys:
                self._keys = new_keys
                self._cache_timestamp = time.time()
                logger.info(f"JWKS keys updated | count={len(new_keys)} | kids={list(new_keys.keys())}")
            else:
                logger.error("JWKS fetch returned no valid keys")
    
    async def get_key(self, kid: str) -> Optional[Any]:
        """
        Get RSA key by kid (Key ID)
        
        Implements stale-while-revalidate pattern:
        - If cache is fresh (<TTL), return immediately
        - If cache is stale but within max_age, return stale + trigger background refresh
        - If cache is expired (>max_age), block and refresh
        
        Lazy initialization: If cache is empty (first use), trigger prewarm
        
        Args:
            kid: Key ID from JWT header
        
        Returns:
            RSA key object or None if key not found
        """
        # Lazy initialization - prewarm on first use if cache is empty
        if not self._keys and self._cache_timestamp == 0:
            logger.info("🔐 LAZY INIT: JWKS cache empty - triggering first-time prewarm")
            await self._refresh_keys()
            if not self._keys:
                logger.error(f"LAZY INIT FAILED: No keys loaded from {self.jwks_url}")
        
        # Fast path: fresh cache
        if self._is_cache_fresh():
            return self._keys.get(kid)
        
        # Stale but within grace period - serve stale + refresh in background
        if not self._is_cache_stale():
            key = self._keys.get(kid)
            # Trigger background refresh (non-blocking)
            asyncio.create_task(self._refresh_keys())
            return key
        
        # Cache expired - block and refresh
        await self._refresh_keys()
        return self._keys.get(kid)
    
    async def prewarm(self):
        """
        Prewarm cache on startup
        
        Raises:
            RuntimeError: If JWKS endpoint is unreachable
        """
        logger.info(f"Prewarming JWKS cache | url={self.jwks_url}")
        
        await self._refresh_keys()
        
        if not self._keys:
            raise RuntimeError(
                f"FATAL: JWKS prewarm failed - no keys loaded from {self.jwks_url}"
            )
        
        logger.info(f"✅ JWKS cache prewarmed | keys={len(self._keys)} | kids={list(self._keys.keys())}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status for /health endpoint
        
        Returns:
            Dict with cache status, last fetch time, errors
        """
        cache_age = time.time() - self._cache_timestamp if self._cache_timestamp else None
        
        return {
            "jwks_cache_healthy": self._is_cache_fresh() or not self._is_cache_stale(),
            "jwks_keys_loaded": len(self._keys),
            "jwks_cache_age_seconds": round(cache_age, 1) if cache_age else None,
            "jwks_last_fetch_success": self._last_fetch_success,
            "jwks_last_error": self._last_fetch_error
        }


# Global singleton instance
jwks_client = JWKSClient()


async def verify_rs256_token(token: str, expected_audience: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Verify RS256 JWT token using JWKS
    
    Args:
        token: JWT token string
        expected_audience: Expected audience claim (optional)
    
    Returns:
        Decoded payload dict or None on validation failure
    """
    try:
        # Get unverified header to extract kid
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        if not kid:
            logger.warning("JWT missing 'kid' in header - cannot validate")
            return None
        
        # Get RSA key by kid
        key = await jwks_client.get_key(kid)
        
        if not key:
            logger.warning(f"Unknown kid={kid} - denying token (CEO directive: deny unknown kids)")
            return None
        
        # Decode and verify token
        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "require_exp": True,
            "require_iat": True,
            "leeway": settings.jwt_clock_skew_leeway  # ±60s clock skew tolerance
        }
        
        decode_kwargs = {
            "algorithms": ["RS256"],
            "options": decode_options,
            "issuer": settings.scholar_auth_issuer
        }
        
        if expected_audience:
            decode_kwargs["audience"] = expected_audience
        
        # Verify with RSA public key
        payload = jwt.decode(token, key, **decode_kwargs)
        
        return payload
    
    except (JWTError, ValueError, KeyError) as e:
        logger.warning(f"JWT RS256 validation failed: {type(e).__name__}: {e}")
        return None
