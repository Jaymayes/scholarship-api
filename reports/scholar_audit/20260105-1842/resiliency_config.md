# Resiliency Configuration
**Audit Date**: 2026-01-05T19:30:00Z

## A2 Scholarship API

### Timeouts
| Operation | Timeout | Source |
|-----------|---------|--------|
| HTTP Client | 10s | httpx default |
| Database Query | 30s | SQLAlchemy pool |
| A8 Event Emission | 5s | services/event_emission.py |
| Stripe API | 10s | Stripe client default |

### Retry/Backoff
| Operation | Retries | Backoff | Source |
|-----------|---------|---------|--------|
| A8 Event Write | 3 | Exponential (1s, 2s, 4s) | event_emission.py |
| Database Connection | 5 | Pool reconnect | SQLAlchemy |
| OIDC JWKS Fetch | 2 | 1s fixed | auth middleware |

### Circuit Breakers
| Circuit | State | Trip Threshold | Recovery |
|---------|-------|----------------|----------|
| A8 Telemetry | CLOSED | 5 failures/60s | 30s half-open |
| Stripe API | N/A | No breaker | Direct calls |

### Fallback Behavior
| Scenario | Fallback | Notes |
|----------|----------|-------|
| A8 unavailable | Local DB write | `business_events` table |
| A1 JWKS unreachable | Cached keys (5m TTL) | In-memory cache |
| Database down | 503 Service Unavailable | No local fallback |

## A7 Auto Page Maker (Issue B)

### Current Config (PROBLEMATIC)
- Synchronous third-party calls on request path
- No circuit breaker on SendGrid
- P95 = 234ms (exceeds 150ms target)

### Recommended Config
- Async ingestion with BackgroundTasks
- Circuit breaker: 3 failures → open for 30s
- Target P95 ≤ 100ms after refactor

## Fleet-wide Observations

- All apps use Replit-managed HTTPS (TLS 1.3)
- No custom circuit breaker libraries detected in most apps
- Rate limiting: A2 uses in-memory (DISABLE_RATE_LIMIT_BACKEND=true)

## Staging Fault Simulation Results

Not performed in this audit (would require induced faults on live services).
Recommendation: Set up isolated staging environment for fault injection testing.
