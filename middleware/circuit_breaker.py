"""
Circuit Breaker Pattern - CEO Directive (Gate 0 Requirement)

Prevents cascading failures by monitoring failure rates and temporarily
blocking requests when thresholds are exceeded.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failure threshold exceeded, requests fail fast
- HALF_OPEN: Testing if service recovered, limited requests allowed
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests (fail fast)
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is OPEN"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation with exponential backoff
    
    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting recovery (HALF_OPEN)
        recovery_threshold: Successes needed in HALF_OPEN to close circuit
        name: Identifier for logging
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_threshold: int = 2,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_threshold = recovery_threshold
        self.name = name
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
        
        # Concurrency safety
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args, **kwargs: Arguments for func
        
        Returns:
            Result of func
        
        Raises:
            CircuitBreakerError: If circuit is OPEN
            Exception: Original exception from func (if circuit allows call)
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and time.time() - self.last_failure_time > self.timeout:
                    logger.info(
                        f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN "
                        f"(timeout expired after {self.timeout}s)"
                    )
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.last_state_change = time.time()
                else:
                    # Circuit is OPEN and timeout not expired - fail fast
                    time_remaining = self.timeout - (time.time() - (self.last_failure_time or time.time()))
                    logger.warning(
                        f"Circuit breaker '{self.name}': Blocking request "
                        f"(OPEN, retry in {time_remaining:.1f}s)"
                    )
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Retry in {time_remaining:.1f}s"
                    )
        
        # Attempt call
        try:
            result = await func(*args, **kwargs)
            
            # Success - update state
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    logger.debug(
                        f"Circuit breaker '{self.name}': Success in HALF_OPEN "
                        f"({self.success_count}/{self.recovery_threshold})"
                    )
                    
                    if self.success_count >= self.recovery_threshold:
                        logger.info(
                            f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED "
                            f"(recovery successful)"
                        )
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                        self.success_count = 0
                        self.last_state_change = time.time()
                
                elif self.state == CircuitState.CLOSED:
                    # Reset failure count on success
                    if self.failure_count > 0:
                        logger.debug(
                            f"Circuit breaker '{self.name}': Resetting failure count "
                            f"({self.failure_count} -> 0)"
                        )
                        self.failure_count = 0
            
            return result
        
        except Exception as e:
            # Failure - update state
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                logger.warning(
                    f"Circuit breaker '{self.name}': Failure {self.failure_count}/{self.failure_threshold} "
                    f"({type(e).__name__}: {str(e)[:100]})"
                )
                
                if self.state == CircuitState.HALF_OPEN:
                    # Failed during recovery - back to OPEN
                    logger.error(
                        f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN "
                        f"(recovery failed)"
                    )
                    self.state = CircuitState.OPEN
                    self.failure_count = 0  # Reset for next recovery attempt
                    self.success_count = 0
                    self.last_state_change = time.time()
                
                elif self.failure_count >= self.failure_threshold:
                    # Threshold exceeded - open circuit
                    logger.error(
                        f"Circuit breaker '{self.name}': CLOSED -> OPEN "
                        f"(failure threshold {self.failure_threshold} exceeded)"
                    )
                    self.state = CircuitState.OPEN
                    self.last_state_change = time.time()
            
            raise
    
    def get_status(self) -> dict:
        """Get current circuit breaker status for monitoring"""
        uptime = time.time() - self.last_state_change
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_threshold": self.recovery_threshold,
            "timeout": self.timeout,
            "last_failure_time": self.last_failure_time,
            "state_uptime_seconds": round(uptime, 2),
            "is_healthy": self.state == CircuitState.CLOSED
        }


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60,
    recovery_threshold: int = 2,
    name: str = "default"
):
    """
    Decorator for applying circuit breaker to async functions
    
    Example:
        @circuit_breaker(failure_threshold=3, timeout=30, name="jwks_fetch")
        async def fetch_jwks():
            # Your code here
            pass
    """
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        recovery_threshold=recovery_threshold,
        name=name
    )
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        
        # Attach circuit breaker instance for monitoring
        wrapper.circuit_breaker = cb
        return wrapper
    
    return decorator


# Global circuit breakers for common dependencies
jwks_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    recovery_threshold=2,
    name="jwks_fetch"
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=10,
    timeout=30,
    recovery_threshold=3,
    name="database"
)

external_api_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=120,
    recovery_threshold=1,
    name="external_api"
)
