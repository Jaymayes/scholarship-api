"""
JWT Replay Protection Service - QA FIX Implementation
Implements jti (JWT ID) cache for replay protection in production
"""

import logging
import time

import redis

from config.settings import settings

logger = logging.getLogger(__name__)

class JWTReplayProtectionService:
    """
    QA FIX: JWT replay protection using Redis cache
    Prevents replay attacks by tracking used JWT IDs (jti claims)
    """

    def __init__(self):
        self.redis_client = None
        self.clock_skew_seconds = settings.jwt_clock_skew_seconds
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection for jti cache"""
        try:
            if settings.environment.value == "production" or settings.jwt_require_jti:
                self.redis_client = redis.Redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("✅ JWT replay protection Redis backend connected")
            else:
                logger.info("ℹ️  JWT replay protection disabled in development mode")
        except Exception as e:
            if settings.environment.value == "production":
                logger.error(f"❌ PRODUCTION ERROR: JWT replay protection Redis required: {e}")
                raise RuntimeError(f"JWT replay protection Redis backend required: {e}")
            logger.warning(f"⚠️  JWT replay protection unavailable: {e}")

    def is_token_replayed(self, jti: str, exp: int, iat: int | None = None) -> bool:
        """
        QA FIX: Check if JWT ID has been used before (replay detection)

        Args:
            jti: JWT ID claim (unique token identifier)
            exp: Expiration time (Unix timestamp)
            iat: Issued at time (Unix timestamp, optional)

        Returns:
            True if token is replayed (should reject), False if token is valid
        """
        if not self.redis_client or not jti:
            # If Redis unavailable or no jti, allow (graceful degradation)
            return False

        try:
            # Calculate TTL: token expiry + clock skew allowance
            current_time = int(time.time())
            ttl_seconds = max(exp - current_time + self.clock_skew_seconds, 60)

            # Attempt atomic SET-if-not-exists
            cache_key = f"jti:{jti}"
            was_set = self.redis_client.set(
                cache_key,
                current_time,
                ex=ttl_seconds,
                nx=True  # Only set if key doesn't exist
            )

            if was_set:
                # Token is new (first use)
                logger.debug(f"JWT token {jti[:8]}... marked as used")
                return False
            # Token already exists (replay attempt)
            logger.warning(f"🚨 JWT REPLAY DETECTED: Token {jti[:8]}... already used")
            self._increment_replay_counter()
            return True

        except Exception as e:
            logger.error(f"JWT replay protection error: {e}")
            # Fail open in case of Redis issues (availability over security)
            return False

    def _increment_replay_counter(self):
        """Increment replay prevention counter for monitoring"""
        try:
            if self.redis_client:
                self.redis_client.incr("jwt_replays_prevented", amount=1)
                # Set expiry if it's a new counter
                self.redis_client.expire("jwt_replays_prevented", 86400)  # 24 hours
        except Exception as e:
            logger.debug(f"Failed to increment replay counter: {e}")

    def get_replay_stats(self) -> dict:
        """Get replay prevention statistics for monitoring"""
        try:
            if not self.redis_client:
                return {"replays_prevented": 0, "status": "disabled"}

            replays_prevented = self.redis_client.get("jwt_replays_prevented") or "0"
            active_tokens = len(self.redis_client.keys("jti:*"))

            return {
                "replays_prevented": int(replays_prevented),
                "active_tokens_tracked": active_tokens,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get replay stats: {e}")
            return {"replays_prevented": 0, "status": "error"}

    def cleanup_expired_tokens(self):
        """Manual cleanup of expired tokens (Redis handles this automatically)"""
        # Redis handles TTL expiration automatically, but this method
        # can be used for manual cleanup if needed
        try:
            if self.redis_client:
                # Get all jti keys and check for expired ones
                jti_keys = self.redis_client.keys("jti:*")
                int(time.time())

                for key in jti_keys:
                    ttl = self.redis_client.ttl(key)
                    if ttl == -1:  # No expiry set
                        self.redis_client.delete(key)

                logger.debug(f"JWT cleanup completed, checked {len(jti_keys)} tokens")
        except Exception as e:
            logger.error(f"JWT cleanup error: {e}")

# Global instance
jwt_replay_protection = JWTReplayProtectionService()
