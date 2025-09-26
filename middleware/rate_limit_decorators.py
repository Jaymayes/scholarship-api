"""
Safe Rate Limit Decorators
Handles None limiter gracefully for test environments
"""

import functools

from middleware.rate_limiting import get_rate_limit_for_environment, limiter


def safe_rate_limit(limit: str):
    """Safe rate limit decorator that handles None limiter"""
    if limiter is None:
        # Return no-op decorator when rate limiting is disabled
        def no_op_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return no_op_decorator

    # Apply actual rate limiting
    adjusted_limit = get_rate_limit_for_environment(limit)
    return limiter.limit(adjusted_limit)

# Pre-configured decorators for common use cases
def database_rate_limit():
    """Standard rate limit for database endpoints"""
    return safe_rate_limit("300/minute")

def low_database_rate_limit():
    """Lower rate limit for resource-intensive database operations"""
    return safe_rate_limit("100/minute")

def moderate_rate_limit():
    """Moderate rate limit for general endpoints"""
    return safe_rate_limit("60/minute")
