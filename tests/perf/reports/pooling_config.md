# Database Pooling Configuration
**Incident ID**: CIR-20260119-001
**Timestamp**: 2026-01-19T15:44:54Z

## Required Configuration (per SEV-2 directive)

```python
# SQLAlchemy Engine Configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # max=10 per instance
    pool_pre_ping=True,     # keepalive=on
    pool_recycle=300,       # 5 min recycle
    pool_timeout=3,         # acquireTimeout=3s
    max_overflow=0,         # no overflow
    connect_args={
        "options": "-c statement_timeout=5000"  # 5s statement timeout
    }
)
```

## Health Markers (add to /health)

```python
{
    "db_connected": true,
    "pool_in_use": 2,
    "pool_idle": 8,
    "pool_size": 10
}
```

## Circuit Breaker Profile

| Parameter | Value |
|-----------|-------|
| Open on | 3 consecutive 5xx/timeouts |
| Cooldown | 60s |
| Backoff | Exponential with jitter |
| Metrics | Emit to A8 |

## Rate Limiting

| Parameter | Value |
|-----------|-------|
| Per-service ceiling | 50 rps |
| Burst | 20 |
| Algorithm | Token bucket |
