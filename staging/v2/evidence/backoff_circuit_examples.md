# Backoff + Circuit Breaker Examples

**Protocol**: AGENT3_HANDSHAKE v30
**Location**: staging/v2/shared/utils/resilience.py

---

## 1. Simple Retry with Exponential Backoff

```python
from shared.utils.resilience import retry_with_backoff

async def fetch_scholarships(query: str):
    async def api_call():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DATASERVICE_URL}/scholarships/match?query={query}")
            response.raise_for_status()
            return response.json()
    
    return await retry_with_backoff(
        api_call,
        max_attempts=3,
        base_delay=0.5,
        max_delay=4.0
    )
```

---

## 2. Circuit Breaker for External APIs

```python
from shared.utils.resilience import CircuitBreaker, with_circuit_breaker

# Define circuit breaker (5 failures → open for 60s)
openai_circuit = CircuitBreaker(
    name="openai",
    failure_threshold=5,
    recovery_timeout=60.0,
    half_open_max_calls=3
)

@with_circuit_breaker(openai_circuit)
async def call_openai(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]}
        )
        return response.json()
```

---

## 3. Resilient HTTP Client (DataService ←→ Orchestrator)

```python
from shared.utils.resilience import ResilientClient, dataservice_circuit

# Create client with circuit breaker
client = ResilientClient(
    base_url="https://saa-core-data-v2-jamarrlmayes.replit.app",
    circuit_breaker=dataservice_circuit,
    timeout=10.0,
    max_retries=3
)

# Use client for API calls
async def signup_student(email: str, age: int):
    response = await client.post(
        "/student/signup",
        json={"email": email, "age": age},
        headers={"X-API-Key": DATASERVICE_API_KEY}
    )
    return response.json()
```

---

## 4. Stripe with Circuit Breaker (Orchestrator → Stripe)

```python
from shared.utils.resilience import stripe_circuit, retry_with_backoff
import stripe

async def create_checkout_session(user_id: str, amount: int):
    async def _call():
        return stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Credits"},
                    "unit_amount": amount
                },
                "quantity": 1
            }],
            mode="payment",
            success_url="https://app.scholaraiadvisor.com/success",
            cancel_url="https://app.scholaraiadvisor.com/cancel",
            metadata={"user_id": user_id}
        )
    
    return await retry_with_backoff(
        _call,
        max_attempts=3,
        circuit_breaker=stripe_circuit
    )
```

---

## 5. Combined Pattern (Full Flow)

```python
from shared.utils.resilience import (
    ResilientClient,
    CircuitBreaker,
    retry_with_backoff,
    exponential_backoff_with_jitter
)

# Service-specific circuits
dataservice_circuit = CircuitBreaker(name="dataservice", failure_threshold=5, recovery_timeout=15.0)
orchestrator_circuit = CircuitBreaker(name="orchestrator", failure_threshold=3, recovery_timeout=30.0)

# Clients
dataservice = ResilientClient(
    base_url=os.environ["DATASERVICE_URL"],
    circuit_breaker=dataservice_circuit
)

async def process_document(user_id: str, document_id: str):
    # Step 1: Get user features from DataService
    user = await dataservice.get(f"/users/{user_id}")
    
    # Step 2: Run NLP analysis (with manual retry)
    async def analyze():
        # Analysis logic here
        pass
    
    features = await retry_with_backoff(
        analyze,
        max_attempts=3,
        base_delay=1.0,
        max_delay=5.0
    )
    
    # Step 3: Store features
    await dataservice.post(
        f"/users/{user_id}/features",
        json=features
    )
    
    return {"status": "processed", "features": features}
```

---

## Configuration Defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_attempts | 3 | Number of retry attempts |
| base_delay | 0.5s | Initial delay between retries |
| max_delay | 4.0s | Maximum delay cap |
| jitter_factor | 0.1 | Random jitter (10% of delay) |
| failure_threshold | 5 | Failures before circuit opens |
| recovery_timeout | 30s | Time before half-open |
| half_open_max_calls | 3 | Calls allowed in half-open |

---

## Circuit States

```
CLOSED → (failure_threshold reached) → OPEN
OPEN → (recovery_timeout elapsed) → HALF_OPEN
HALF_OPEN → (success) → CLOSED
HALF_OPEN → (failure) → OPEN
```
