# Business Event Instrumentation - Implementation Guide for App Owners

## Quick Start

This guide shows how to instrument your app (Student Pilot, Provider Register, Scholar Auth, etc.) to emit business events for Executive Command Center KPI reporting.

---

## 1. Load System Prompts

Each app must load TWO prompt files in order:

```python
# Example: Student Pilot
shared_directives = read_file("docs/system-prompts/shared_directives.prompt")
app_specific = read_file("docs/system-prompts/student_pilot.prompt")

system_prompt = f"{shared_directives}\n\n---\n\n{app_specific}"
```

**Cache the merged prompt** with a version hash for performance.

---

## 2. Import Event Helpers

```python
from models.business_events import (
    create_student_signup_event,  # Student Pilot
    create_provider_registered_event,  # Provider Register
    # ... import your app's event helpers
)
from services.event_emission import EventEmissionService

event_emitter = EventEmissionService()
```

---

## 3. Instrument Your Endpoints

### Student Pilot Example: Signup Event

```python
@router.post("/signup")
async def signup(request: Request, data: SignupRequest):
    # Your existing signup logic
    user = create_user(data.email, data.password)
    
    # Extract session tracking
    session_id = request.headers.get("X-Session-ID")
    
    # Emit business event (fire-and-forget)
    event = create_student_signup_event(
        signup_method=data.method,  # "email", "google", "facebook"
        age_bracket=calculate_age_bracket(data.age),
        consent_required=data.age < 13,
        actor_id=user.id,
        session_id=session_id
    )
    await event_emitter.emit(event)
    
    return {"user_id": user.id}
```

### Provider Register Example: Fee Revenue Tracking

```python
@router.post("/scholarships")
async def create_scholarship(request: Request, data: ScholarshipCreateRequest, provider: Provider):
    # Your existing scholarship creation logic
    scholarship = save_scholarship(data)
    
    # CRITICAL: Compute fee server-side (NEVER trust client)
    fee_base_usd = data.award_amount  # or listing fee
    fee_pct = 0.03  # Always 3%
    fee_usd = fee_base_usd * fee_pct
    
    # Emit revenue event
    session_id = request.headers.get("X-Session-ID")
    event = create_scholarship_posted_event(
        scholarship_id=scholarship.id,
        scholarship_name=scholarship.name,
        fee_base_usd=fee_base_usd,
        fee_pct=fee_pct,
        fee_usd=fee_usd,  # Computed server-side!
        actor_id=provider.id,
        org_id=provider.org_id,
        session_id=session_id
    )
    await event_emitter.emit(event)
    
    return {"scholarship_id": scholarship.id}
```

---

## 4. Revenue Event Requirements

### B2C Revenue (Student Pilot)

**credit_purchased:**
```python
event = create_credit_purchased_event(
    payment_id="pay_abc123",
    credit_amount=50,
    revenue_usd=25.00,  # Actual payment amount
    payment_method="card"
)
```

**application_submitted:**
```python
event = create_application_submitted_event(
    application_id="app_xyz",
    scholarship_id="sch_123",
    credit_spent=5,
    revenue_usd=2.50,  # Credit value spent
    application_time_minutes=45.2
)
```

### B2B Revenue (Provider Register)

**scholarship_posted:**
```python
fee_usd = fee_base_usd * 0.03  # Always compute server-side!
event = create_scholarship_posted_event(
    scholarship_id="sch_789",
    fee_base_usd=1000.00,
    fee_pct=0.03,
    fee_usd=30.00  # Server-computed
)
```

---

## 5. Session ID Extraction

Add this utility to your app:

```python
def extract_session_id(request: Request) -> Optional[str]:
    """Extract session ID for user journey tracking"""
    # Priority 1: Explicit header
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return session_id
    
    # Priority 2: Session cookie
    session_cookie = request.cookies.get("session_id")
    if session_cookie:
        return session_cookie
    
    return None
```

**Use it in every instrumented endpoint:**
```python
session_id = extract_session_id(request)
```

---

## 6. Required Events by App

### Student Pilot (B2C)
1. `student_signup` - User registration
2. `profile_completed` - Profile ≥70% complete
3. `match_viewed` - Student views match
4. `credit_purchased` - **REVENUE** (payment captured)
5. `credit_spent` - Credit consumption
6. `application_submitted` - **REVENUE** (credits consumed)

### Provider Register (B2B)
1. `provider_registered` - Organization signs up
2. `provider_verified` - KYC/verification complete
3. `provider_active` - First scholarship posted
4. `scholarship_posted` - **REVENUE** (3% fee captured)
5. `provider_churned` - Account closed

### Scholarship API (Engagement)
1. `scholarship_viewed` - Detail page view
2. `scholarship_saved` - User saves scholarship
3. `match_generated` - Recommendations generated
4. `application_started` - Application begun
5. `application_submitted` - Application sent

### Scholar Auth (Identity)
1. `email_verified` - Email confirmation
2. `consent_recorded` - COPPA/FERPA consent
3. `login_succeeded` - Successful login
4. `login_failed` - Failed login attempt

### Auto Page Maker (SEO)
1. `page_published` - New SEO page live
2. `page_updated` - Page content refreshed
3. `page_indexed` - Google/Bing indexed
4. `serp_click` - Organic search click
5. `conversion_attributed` - SEO → revenue

### Scholarship Agent (Growth)
1. `campaign_launched` - New campaign started
2. `campaign_step_completed` - Funnel step
3. `ab_test_started` - Test variant assigned
4. `ab_test_converted` - Conversion in variant
5. `link_clicked` - UTM link clicked

### Scholarship Sage (AI Advisor)
1. `guidance_session_started` - AI guidance begins
2. `guidance_recommendation_viewed` - Recommendation shown
3. `checklist_created` - Application checklist generated
4. `checklist_completed` - Checklist finished

---

## 7. Verification Steps

### Step 1: Verify Prompt Loading
```python
GET /api/prompts
# Should return list of 9 loaded prompts

GET /api/prompts/:app
# Should return merged prompt for your app

GET /api/prompts/verify
# Should return success with hashes
```

### Step 2: Verify Event Emission
```sql
-- Check events are writing
SELECT COUNT(*) FROM business_events 
WHERE ts > NOW() - interval '24 hours';

-- Check your app's events
SELECT event_name, COUNT(*) 
FROM business_events 
WHERE app = 'student_pilot' 
GROUP BY event_name;
```

### Step 3: Verify Revenue Events
```sql
-- B2C revenue check
SELECT 
    SUM((properties->>'revenue_usd')::numeric) as total_revenue,
    COUNT(*) as transaction_count
FROM business_events
WHERE event_name IN ('credit_purchased', 'application_submitted')
  AND ts > NOW() - interval '24 hours';

-- B2B revenue check
SELECT 
    SUM((properties->>'fee_usd')::numeric) as total_fees,
    COUNT(*) as scholarship_count
FROM business_events
WHERE event_name = 'scholarship_posted'
  AND ts > NOW() - interval '24 hours';
```

---

## 8. Common Pitfalls

### ❌ DON'T: Client-side fee calculation
```python
# BAD - Client can manipulate
fee_usd = data.fee_usd  # From request body
```

### ✅ DO: Server-side fee calculation
```python
# GOOD - Server computes
fee_usd = data.award_amount * 0.03
```

### ❌ DON'T: Missing session_id
```python
event = create_event(..., session_id=None)  # Lost journey context
```

### ✅ DO: Always extract session_id
```python
session_id = extract_session_id(request)
event = create_event(..., session_id=session_id)
```

### ❌ DON'T: Hardcode environment
```python
event.env = "production"  # Wrong for dev/staging
```

### ✅ DO: Use settings
```python
# Event models automatically use settings.environment
```

---

## 9. Testing Your Implementation

### Manual Test Flow

1. **Trigger an endpoint** (e.g., POST /signup)
2. **Check logs** for "✅ Event emitted"
3. **Query database:**
   ```sql
   SELECT * FROM business_events 
   ORDER BY ts DESC LIMIT 10;
   ```
4. **Verify fields:** request_id, actor_id, session_id, properties

### Automated Test

```python
def test_signup_emits_student_signup_event():
    # Trigger signup
    response = client.post("/signup", json={...})
    
    # Wait for background task
    await asyncio.sleep(0.5)
    
    # Query database
    result = db.execute(
        "SELECT * FROM business_events WHERE event_name = 'student_signup'"
    )
    assert result.rowcount == 1
    event = result.fetchone()
    assert event.properties['signup_method'] == 'email'
```

---

## 10. Executive Command Center Integration

Once your events are emitting, Executive Command Center will automatically:

1. **Aggregate KPIs** from your events
2. **Generate daily briefs** at 09:00 UTC
3. **Post to Slack** (#executive-dashboard)
4. **Track SLO breaches** (uptime, P95, errors)
5. **Calculate revenue** (B2C + B2B)

**Your events power the CEO's dashboard!**

---

## 11. Support & Troubleshooting

### Circuit Breaker Tripped
```
🔴 Event emission circuit breaker OPEN
```
**Fix:** Check DATABASE_URL configuration, restart service

### Events Not Persisting
```sql
SELECT COUNT(*) FROM business_events;  -- Returns 0
```
**Fix:** Check event_emitter is initialized, verify DATABASE_URL

### Missing Revenue Data
```
Revenue (24h): $0.00
```
**Fix:** Ensure revenue_usd is populated in credit_purchased/application_submitted/scholarship_posted events

---

## Quick Checklist

- [ ] Load shared_directives.prompt + app-specific prompt
- [ ] Import event helpers and EventEmissionService
- [ ] Add session ID extraction utility
- [ ] Instrument all required endpoints (see section 6)
- [ ] Compute revenue server-side (B2C/B2B)
- [ ] Test with manual endpoint calls
- [ ] Verify events in business_events table
- [ ] Run verification SQL queries
- [ ] Confirm events appear in Executive Command Center

---

**Questions?** Check `docs/BUSINESS_EVENTS_INSTRUMENTATION_GUIDE.md` or ask in #engineering-kpis Slack channel.
