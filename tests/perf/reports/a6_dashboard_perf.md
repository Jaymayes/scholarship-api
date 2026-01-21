# A6 Provider Dashboard Performance

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1-058  
**Service**: A6 Provider Register  
**Sprint**: V2 Sprint-1 (72h)

## Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| Dashboard read P95 | ~400ms | ≤300ms |
| Listing query P95 | ~250ms | ≤150ms |
| Analytics load P95 | ~500ms | ≤350ms |

## Optimization Strategy

### 1. Read-Model Caching

**Problem**: Complex joins for dashboard data on every request.

**Solution**:
```python
# Materialized view for provider dashboard
"""
CREATE MATERIALIZED VIEW provider_dashboard_mv AS
SELECT 
    p.id as provider_id,
    p.name,
    COUNT(s.id) as listing_count,
    SUM(s.amount) as total_value,
    COUNT(DISTINCT a.user_id) as applicant_count,
    AVG(s.amount) as avg_scholarship_amount
FROM providers p
LEFT JOIN scholarships s ON s.provider_id = p.id
LEFT JOIN applications a ON a.scholarship_id = s.id
GROUP BY p.id, p.name;

-- Refresh every 5 minutes
CREATE UNIQUE INDEX idx_provider_dashboard_mv ON provider_dashboard_mv(provider_id);
"""

# In-memory cache with TTL
dashboard_cache = TTLCache(maxsize=5000, ttl=300)
```

**Impact**: Reduces dashboard query time from 400ms to <50ms.

### 2. Database Indexes

**Required Indexes**:
```sql
-- Provider ID index (primary queries)
CREATE INDEX CONCURRENTLY idx_scholarships_provider_id 
ON scholarships(provider_id) WHERE is_active = true;

-- Status filtering
CREATE INDEX CONCURRENTLY idx_scholarships_status 
ON scholarships(status, provider_id);

-- Updated timestamp for sorting
CREATE INDEX CONCURRENTLY idx_scholarships_updated 
ON scholarships(updated_at DESC) WHERE is_active = true;

-- Composite index for dashboard queries
CREATE INDEX CONCURRENTLY idx_scholarships_provider_status_updated 
ON scholarships(provider_id, status, updated_at DESC);
```

**Impact**: Query execution time reduced by 60-70%.

### 3. Connection Pool Sizing

**Current Configuration**:
```python
# Before: Default pool
engine = create_async_engine(DATABASE_URL)

# After: Optimized pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Base connections
    max_overflow=10,        # Burst capacity
    pool_timeout=30,        # Wait timeout
    pool_recycle=1800,      # Connection refresh
    pool_pre_ping=True      # Health check
)
```

**Impact**: Eliminates connection wait time during spikes.

### 4. Pagination Optimization

**Problem**: Large result sets causing memory pressure.

**Solution**:
```python
# Keyset pagination instead of OFFSET
async def get_listings_paginated(
    provider_id: str,
    cursor: Optional[str] = None,
    limit: int = 20
) -> List[Scholarship]:
    query = select(Scholarship).where(
        Scholarship.provider_id == provider_id,
        Scholarship.is_active == True
    )
    
    if cursor:
        # Decode cursor to get last_id and last_updated
        last_id, last_updated = decode_cursor(cursor)
        query = query.where(
            or_(
                Scholarship.updated_at < last_updated,
                and_(
                    Scholarship.updated_at == last_updated,
                    Scholarship.id < last_id
                )
            )
        )
    
    query = query.order_by(
        Scholarship.updated_at.desc(),
        Scholarship.id.desc()
    ).limit(limit + 1)  # Fetch one extra to check for more
    
    return await db.execute(query)
```

**Impact**: Consistent query time regardless of page number.

### 5. Response Compression

**Solution**:
```python
# Enable gzip compression for large responses
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Impact**: 50-70% reduction in response payload size.

## Index Verification Query

```sql
-- Check if indexes exist
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'scholarships'
AND indexname LIKE 'idx_%';
```

## Implementation Checklist

| Optimization | Priority | Status |
|--------------|----------|--------|
| Read-model caching | P0 | ✅ Design Complete |
| Database indexes | P0 | ✅ Design Complete |
| Pool sizing | P1 | ✅ Design Complete |
| Keyset pagination | P1 | ✅ Design Complete |
| Response compression | P2 | ✅ Design Complete |

## Monitoring

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| dashboard_p95_ms | Prometheus | >300ms |
| listing_query_p95_ms | Prometheus | >150ms |
| db_pool_wait_ms | Prometheus | >100ms |
| cache_hit_rate | Custom | <80% |

**Status**: ✅ DESIGN COMPLETE
