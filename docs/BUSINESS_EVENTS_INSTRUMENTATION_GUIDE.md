# Business Events Instrumentation Guide
**CEO Directive: Complete within 72 hours for revenue visibility**

## Overview
This guide documents where to add business event instrumentation across the Scholarship API to unlock executive KPI reporting and revenue tracking.

## Required Events (5 Total)

### 1. scholarship_viewed ✅ PARTIALLY IMPLEMENTED
**Purpose:** Track when users view scholarship details
**Where to add:**
- ✅ `routers/scholarships.py:get_scholarship()` - Already instrumented (example implementation)
- ⏳ `routers/search.py:search_scholarships_get()` - Add to each result returned
- ⏳ `routers/search.py:search_scholarships_post()` - Add to each result returned
- ⏳ `routers/recommendations.py` - Add when recommendations are returned

**Example:**
```python
from services.event_emission import emit_scholarship_viewed
import asyncio

# In endpoint handler:
asyncio.create_task(emit_scholarship_viewed(
    scholarship_id=scholarship_id,
    source="search|recommendation|detail|browse",
    match_score=0.85,  # Include if available from ranking
    actor_id=user_id,
    session_id=session_id  # Extract from headers
))
```

**KPI Impact:** Enables tracking of view-to-save conversion rate

---

### 2. scholarship_saved ⏳ NOT IMPLEMENTED
**Purpose:** Track when users bookmark/save scholarships for later
**Where to add:**
- ⏳ Add a new POST endpoint: `/api/v1/scholarships/{id}/save`
- ⏳ Or instrument existing save functionality if it exists

**Example:**
```python
from services.event_emission import emit_scholarship_saved

@router.post("/scholarships/{scholarship_id}/save")
async def save_scholarship(
    scholarship_id: str,
    current_user: User = Depends(require_auth())
):
    # Save to database...
    
    # Emit event
    asyncio.create_task(emit_scholarship_saved(
        scholarship_id=scholarship_id,
        match_score=match_score,  # From user's match profile
        eligibility_score=eligibility_result.match_score,
        actor_id=current_user.id,
        session_id=session_id
    ))
    
    return {"status": "saved"}
```

**KPI Impact:** Critical for conversion funnel (view → save → apply)

---

### 3. match_generated ⏳ NOT IMPLEMENTED
**Purpose:** Track AI-powered scholarship matching runs
**Where to add:**
- ⏳ `routers/recommendations.py:get_recommendations()` - After generating matches
- ⏳ `routers/predictive_matching.py` - If predictive matching endpoint exists
- ⏳ Any AI/ML-powered match generation endpoints

**Example:**
```python
from services.event_emission import emit_match_generated
import time

# Before matching:
start_time = time.time()

# Generate matches...
matches = recommendation_service.generate_matches(user_profile)

# Calculate metrics
processing_time_ms = (time.time() - start_time) * 1000
match_quality_avg = sum(m.score for m in matches) / len(matches)

# Emit event
asyncio.create_task(emit_match_generated(
    student_id=user_profile.id,
    num_matches=len(matches),
    match_quality_avg=match_quality_avg,
    processing_time_ms=processing_time_ms
))
```

**KPI Impact:** Track match quality and AI service performance

---

### 4. application_started ⏳ NOT IMPLEMENTED
**Purpose:** Track when users begin applying to scholarships
**Where to add:**
- ⏳ Add new POST endpoint: `/api/v1/applications/{scholarship_id}/start`
- ⏳ This signals user intent to apply

**Example:**
```python
from services.event_emission import emit_application_started
from datetime import datetime

@router.post("/applications/{scholarship_id}/start")
async def start_application(
    scholarship_id: str,
    current_user: User = Depends(require_auth())
):
    # Create application draft...
    
    # Calculate time since save (if available)
    saved_at = get_saved_timestamp(current_user.id, scholarship_id)
    time_since_save_hours = None
    if saved_at:
        time_since_save_hours = (datetime.utcnow() - saved_at).total_seconds() / 3600
    
    # Emit event
    asyncio.create_task(emit_application_started(
        scholarship_id=scholarship_id,
        time_since_save_hours=time_since_save_hours,
        credit_cost=5,  # If credits are required
        actor_id=current_user.id,
        session_id=session_id
    ))
    
    return {"status": "started", "application_id": app_id}
```

**KPI Impact:** Conversion funnel tracking (save → apply rate)

---

### 5. application_submitted ⏳ NOT IMPLEMENTED
**Purpose:** Track completed applications and revenue
**Where to add:**
- ⏳ Add new POST endpoint: `/api/v1/applications/{scholarship_id}/submit`
- ⏳ This is the CRITICAL revenue event

**Example:**
```python
from services.event_emission import emit_application_submitted
from datetime import datetime

@router.post("/applications/{scholarship_id}/submit")
async def submit_application(
    scholarship_id: str,
    application_data: ApplicationData,
    current_user: User = Depends(require_auth())
):
    # Validate application...
    # Submit to scholarship provider...
    # Deduct credits...
    
    started_at = get_application_start_time(application_id)
    application_time_minutes = (datetime.utcnow() - started_at).total_seconds() / 60
    
    credit_spent = 5
    revenue_usd = credit_spent * 0.50  # $0.50 per credit
    
    # Emit event
    asyncio.create_task(emit_application_submitted(
        scholarship_id=scholarship_id,
        application_time_minutes=application_time_minutes,
        credit_spent=credit_spent,
        revenue_usd=revenue_usd,
        actor_id=current_user.id,
        session_id=session_id
    ))
    
    return {"status": "submitted", "application_id": app_id}
```

**KPI Impact:** REVENUE TRACKING - This event unlocks B2C revenue visibility

---

## Implementation Priority

### Phase 1: Critical Path (Next 24 hours)
1. ✅ **scholarship_viewed** - Example implemented in `scholarships.py`
2. ⏳ **scholarship_saved** - Create save endpoint
3. ⏳ **application_submitted** - Revenue tracking

### Phase 2: Funnel Completion (24-48 hours)
4. ⏳ **application_started** - Application intent tracking
5. ⏳ **match_generated** - AI performance metrics

### Phase 3: Complete Coverage (48-72 hours)
6. ⏳ Add `scholarship_viewed` to search results
7. ⏳ Add `scholarship_viewed` to recommendations
8. ⏳ Extract session_id from request headers across all events

---

## Testing Event Emission

### Verify Events in Database
```sql
-- Check if events are being emitted
SELECT 
    event_name,
    COUNT(*) as event_count,
    MAX(ts) as last_event
FROM business_events
WHERE app = 'scholarship_api'
GROUP BY event_name
ORDER BY event_count DESC;

-- View recent scholarship_viewed events
SELECT 
    ts,
    actor_id,
    properties->>'scholarship_id' as scholarship_id,
    properties->>'source' as source,
    properties->>'match_score' as match_score
FROM business_events
WHERE event_name = 'scholarship_viewed'
ORDER BY ts DESC
LIMIT 10;
```

### Test Endpoint
```bash
# Test scholarship detail view (should emit scholarship_viewed)
curl -X GET "http://localhost:5000/api/v1/scholarships/sch_123?user_id=test_user"

# Verify event was created
psql $DATABASE_URL -c "SELECT * FROM business_events WHERE event_name = 'scholarship_viewed' ORDER BY ts DESC LIMIT 1;"
```

---

## KPI Calculations (For Executive Command Center)

Once events are emitting, these KPIs can be calculated:

### scholarship_view_to_save
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN event_name = 'scholarship_saved' THEN actor_id END)::float /
    NULLIF(COUNT(DISTINCT CASE WHEN event_name = 'scholarship_viewed' THEN actor_id END), 0) * 100 
    as view_to_save_rate
FROM business_events
WHERE ts >= NOW() - INTERVAL '24 hours'
AND event_name IN ('scholarship_viewed', 'scholarship_saved');
```

### save_to_apply
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN event_name = 'application_submitted' THEN actor_id END)::float /
    NULLIF(COUNT(DISTINCT CASE WHEN event_name = 'scholarship_saved' THEN actor_id END), 0) * 100
    as save_to_apply_rate
FROM business_events
WHERE ts >= NOW() - INTERVAL '24 hours'
AND event_name IN ('scholarship_saved', 'application_submitted');
```

### match_quality_score
```sql
SELECT 
    AVG((properties->>'match_quality_avg')::float) as avg_match_quality
FROM business_events
WHERE event_name = 'match_generated'
AND ts >= NOW() - INTERVAL '24 hours';
```

### Revenue (24 hour)
```sql
SELECT 
    SUM((properties->>'revenue_usd')::float) as revenue_24h,
    COUNT(*) as applications_submitted
FROM business_events
WHERE event_name = 'application_submitted'
AND ts >= NOW() - INTERVAL '24 hours';
```

---

## Session ID Extraction

To properly track user journeys, extract session_id from headers:

```python
def get_session_id(request: Request) -> Optional[str]:
    """Extract session ID from request headers"""
    # Try cookie first
    session_id = request.cookies.get("session_id")
    if session_id:
        return session_id
    
    # Try header
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return session_id
    
    # Generate new session if none exists
    return str(uuid.uuid4())
```

---

## Monitoring Event Emission Health

### Check Circuit Breaker Status
```python
from services.event_emission import event_emission_service

# In admin endpoint:
status = event_emission_service.get_status()
# Returns: {"enabled": true, "circuit_open": false, "failure_count": 0}
```

### Reset Circuit Breaker (If Needed)
```python
event_emission_service.reset_circuit_breaker()
```

---

## Next Steps

1. **Immediate:** Complete scholarship_saved endpoint implementation
2. **Urgent:** Add application_started and application_submitted endpoints
3. **Important:** Add match_generated to recommendation endpoints
4. **Enhancement:** Extract session_id across all instrumented endpoints
5. **Validation:** Run test queries to verify event data quality

---

## Success Criteria

✅ All 5 required events emitting within 72 hours
✅ business_events table populating with valid data
✅ KPI calculations returning non-zero values
✅ Executive Command Center daily brief shows Scholarship API metrics
✅ No circuit breaker trips (failure_count < 10)
