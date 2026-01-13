"""
Reliability Harness - Backoff + Circuit Breaker Utilities
Protocol: AGENT3_HANDSHAKE v30
"""
import time
import random
import asyncio
from typing import Callable, Any, Optional, TypeVar
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
import httpx

T = TypeVar('T')


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    Prevents cascade failures when external services are down.
    """
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    
    failures: int = field(default=0, init=False)
    last_failure_time: float = field(default=0, init=False)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    half_open_calls: int = field(default=0, init=False)
    
    def can_proceed(self) -> bool:
        """Check if call can proceed through the circuit."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failures = 0
        else:
            self.failures = max(0, self.failures - 1)
    
    def record_failure(self):
        """Record failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN


def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    jitter_factor: float = 0.1
) -> float:
    """
    Calculate delay with exponential backoff and jitter.
    Prevents thundering herd problem.
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = delay * jitter_factor * random.random()
    return delay + jitter


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    circuit_breaker: Optional[CircuitBreaker] = None,
    **kwargs
) -> T:
    """
    Retry async function with exponential backoff and optional circuit breaker.
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        if circuit_breaker and not circuit_breaker.can_proceed():
            raise Exception(f"Circuit breaker '{circuit_breaker.name}' is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if circuit_breaker:
                circuit_breaker.record_success()
            return result
        except Exception as e:
            last_exception = e
            if circuit_breaker:
                circuit_breaker.record_failure()
            
            if attempt < max_attempts - 1:
                delay = exponential_backoff_with_jitter(attempt, base_delay, max_delay)
                await asyncio.sleep(delay)
    
    raise last_exception


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """
    Decorator to wrap async functions with circuit breaker.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not circuit_breaker.can_proceed():
                raise Exception(f"Circuit breaker '{circuit_breaker.name}' is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise
        
        return wrapper
    return decorator


openai_circuit = CircuitBreaker(name="openai", failure_threshold=3, recovery_timeout=60.0)
stripe_circuit = CircuitBreaker(name="stripe", failure_threshold=5, recovery_timeout=30.0)
dataservice_circuit = CircuitBreaker(name="dataservice", failure_threshold=5, recovery_timeout=15.0)


class ResilientClient:
    """
    HTTP client with built-in retry and circuit breaker.
    """
    
    def __init__(
        self,
        base_url: str,
        circuit_breaker: Optional[CircuitBreaker] = None,
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.circuit_breaker = circuit_breaker
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry and circuit breaker."""
        url = f"{self.base_url}{path}"
        
        async def make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
        
        return await retry_with_backoff(
            make_request,
            max_attempts=self.max_retries,
            circuit_breaker=self.circuit_breaker
        )
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)


BACKOFF_CIRCUIT_EXAMPLES = """
# Backoff + Circuit Breaker Examples

## 1. Simple retry with backoff

```python
from shared.utils.resilience import retry_with_backoff

async def fetch_scholarships():
    return await retry_with_backoff(
        api_call,
        max_attempts=3,
        base_delay=0.5,
        max_delay=4.0
    )
```

## 2. Circuit breaker for external APIs

```python
from shared.utils.resilience import CircuitBreaker, with_circuit_breaker

openai_circuit = CircuitBreaker(
    name="openai",
    failure_threshold=3,
    recovery_timeout=60.0
)

@with_circuit_breaker(openai_circuit)
async def call_openai(prompt):
    return await openai_client.chat(prompt)
```

## 3. Resilient HTTP client (DataService ←→ Orchestrator)

```python
from shared.utils.resilience import ResilientClient, dataservice_circuit

client = ResilientClient(
    base_url="https://saa-core-data-v2.replit.app",
    circuit_breaker=dataservice_circuit,
    timeout=10.0,
    max_retries=3
)

response = await client.post("/student/signup", json={"email": "test@example.com"})
```

## 4. Stripe with circuit breaker (Orchestrator → Stripe)

```python
from shared.utils.resilience import stripe_circuit, retry_with_backoff

async def create_checkout_session(user_id, amount):
    async def _call():
        return stripe.checkout.Session.create(...)
    
    return await retry_with_backoff(
        _call,
        max_attempts=3,
        circuit_breaker=stripe_circuit
    )
```
"""
