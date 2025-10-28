# Universal Prompt Rollout Plan (v1.0.0)

## Executive Summary

The **Universal Prompt (v1.0.0)** is production-ready and deployed for Scholarship API. This document outlines the phased rollout plan for all 8 ScholarshipAI apps to achieve the CEO's 72-hour revenue visibility directive.

---

## Current Status (T+0)

### ✅ Scholarship API - COMPLETE
- **Architecture:** Universal (hybrid mode)
- **Verification Hash:** `0d53e9f1ec9d5463`
- **Prompts Loaded:** 2/2 (shared_directives.prompt + universal.prompt)
- **Events Instrumented:** 5/5
  - `match_generated` ✅
  - `scholarship_viewed` ✅
  - `scholarship_saved` ✅
  - `application_started` ✅
  - `application_submitted` (with `revenue_usd`) ✅
- **Revenue Tracking:** Operational (B2C credit consumption)
- **Production Status:** Live on port 5000

---

## Rollout Timeline

### **T+0 to T+24h: Phase 1 - API Apps**

**Apps:** `scholarship_api`, `scholarship_agent`

**Scholarship API Status:**
- ✅ Universal prompt deployed
- ✅ All endpoints operational
- ✅ Revenue events emitting
- ✅ Verification endpoints live

**Scholarship Agent (Next):**
Must implement:
```python
# Required events:
- campaign_launched(campaignId, channel, audience, goal)
- campaign_step_completed(campaignId, step)
- ab_test_started(testId, variantKeys)
- ab_test_converted(testId, variant, conversionEvent)
- lead_captured(source, lead_type)
- link_clicked(campaignId, url, utm, sessionId)
```

**Acceptance Criteria:**
- [ ] `/api/prompts/verify` shows universal architecture
- [ ] Event volumes stable (>100 events/day per app)
- [ ] P95 latency ≤120ms
- [ ] No increase in error rates

---

### **T+24h to T+48h: Phase 2 - Revenue Apps**

**Apps:** `student_pilot`, `provider_register`

**Critical Path: Revenue Tracking**

#### Student Pilot (B2C)
```python
# Cash-in event (REVENUE)
credits_purchased(
    userId="user_123",
    credits=10,
    revenue_usd=25.00  # 10 credits at $2.50 each
)

# Consumption event (USAGE)
application_submitted(
    userId="user_123",
    scholarshipId="sch_001",
    revenue_usd=5.00  # 2 credits consumed at $2.50 each
)
```

#### Provider Register (B2B)
```python
# Platform fee event (REVENUE)
scholarship_posted(
    scholarshipId="sch_001",
    providerId="provider_123",
    award_amount=10000.00,
    fee_pct=0.03,
    fee_usd=300.00  # Server computes: 10000 * 0.03
)
```

**Acceptance Criteria:**
- [ ] First `revenue_usd > 0` event from Student Pilot
- [ ] First `fee_usd > 0` event from Provider Register
- [ ] Database query confirms revenue:
  ```sql
  SELECT 
    DATE(ts) as date,
    SUM(CAST(properties->>'revenue_usd' AS DECIMAL)) as b2c_revenue,
    SUM(CAST(properties->>'fee_usd' AS DECIMAL)) as b2b_revenue
  FROM business_events
  WHERE event_name IN ('credits_purchased', 'scholarship_posted')
  GROUP BY DATE(ts);
  ```

---

### **T+48h to T+72h: Phase 3 - Supporting Apps**

**Apps:** `scholar_auth`, `auto_page_maker`, `scholarship_sage`, `executive_command_center`

#### Scholar Auth
```python
# Identity events
- auth_started(userId?)
- auth_success(userId)
- auth_failed(reason)
```

#### Auto Page Maker (SEO/Attribution)
```python
# Growth events
- page_published(slug, topic, intent, est_read_time)
- page_indexed(slug, engine, rank, indexedAt)
- page_viewed(slug, sessionId, referrer, utm, deviceType, location)
- lead_captured(leadId, sourceSlug, sessionId, leadType, attributionPath)
```

#### Scholarship Sage (AI Advisor)
```python
# Guidance events
- recommendation_shown(userId, scholarshipId, rationaleTag)
- recommendation_accepted(userId, scholarshipId)
- checklist_created(userId, scholarshipId, checklistId, itemCount)
- checklist_completed(userId, checklistType)
```

#### Executive Command Center (KPI Aggregation)
```python
# Daily brief (09:00 UTC)
- kpi_generated(window, mrr, arr, cac, arpu)
- daily_brief_posted(timestamp, channel)
- scheduler_job_run(jobName, status, duration_ms)
```

**Acceptance Criteria:**
- [ ] All 8 apps emitting events to `business_events`
- [ ] Executive Command Center generates first KPI report
- [ ] Daily brief at 09:00 UTC shows real revenue
- [ ] No SLO breaches or `perf_observed` anomalies

---

## Technical Implementation Guide

### 1. Install Universal Prompt

```bash
# Already in: docs/system-prompts/universal.prompt
# Size: 10,790 bytes
# Hash: d68207a95112c9bb
```

### 2. Configure App Key

**Option A: Environment Variable (Recommended)**
```bash
# Add to .env
APP_NAME=scholarship_api  # or student_pilot, provider_register, etc.
```

**Option B: Runtime Parameter**
```python
# In your app bootstrap
app_key = os.getenv("APP_NAME", "scholarship_api")
```

### 3. Load Prompts at Startup

```python
from pathlib import Path
import hashlib

def load_universal_prompt(app_key: str):
    """Load shared directives + app overlay from universal prompt"""
    
    # Load shared directives
    shared_path = Path("docs/system-prompts/shared_directives.prompt")
    shared_content = shared_path.read_text()
    
    # Load universal prompt
    universal_path = Path("docs/system-prompts/universal.prompt")
    universal_content = universal_path.read_text()
    
    # Merge for runtime
    merged_prompt = f"{shared_content}\n\n---\n\n{universal_content}"
    
    # Calculate hash
    combined_hash = hashlib.sha256(merged_prompt.encode()).hexdigest()[:16]
    
    # Emit bootstrap event
    emit_event({
        "event_name": "overlay_selected",
        "app": app_key,
        "properties": {
            "hash": combined_hash,
            "loader": "universal",
            "mode": "active"
        }
    })
    
    return merged_prompt, combined_hash
```

### 4. Verify Prompt Loading

```bash
# Check verification endpoint
curl http://localhost:5000/api/prompts/verify

# Should return:
# {
#   "app": "scholarship_api",
#   "architecture": "universal",
#   "prompts_loaded": 2,
#   "verification_hash": "0d53e9f1ec9d5463"
# }
```

### 5. Extract App Overlay (Debug)

```bash
# View your app's specific overlay
curl http://localhost:5000/api/prompts/overlay/scholarship_api

# Returns just the [APP: scholarship_api] section
```

---

## Event Emission Standards

### Required Fields (All Events)
```python
{
    "event_name": "scholarship_viewed",  # Required
    "app": "scholarship_api",            # From APP_NAME env var
    "ts": "2025-10-28T10:30:00Z",       # ISO8601, server-issued
    "request_id": "req_abc123",          # From X-Request-ID header
    "session_id": "sess_xyz789",         # From X-Session-ID header
    "actor_type": "User",                # User|System|Anonymous
    "actor_id": "user_123",              # Optional: from X-User-ID header
    "properties": {                      # App-specific data
        "scholarship_id": "sch_001"
    }
}
```

### Revenue Events (Special Handling)

**B2C Revenue (credits_purchased):**
```python
{
    "event_name": "credits_purchased",
    "app": "student_pilot",
    "actor_id": "user_123",
    "properties": {
        "credits": 10,
        "revenue_usd": 25.00  # MUST be present for B2C revenue
    }
}
```

**B2B Revenue (scholarship_posted):**
```python
{
    "event_name": "scholarship_posted",
    "app": "provider_register",
    "org_id": "org_456",  # B2B events use org_id
    "properties": {
        "scholarship_id": "sch_001",
        "provider_id": "provider_123",
        "award_amount": 10000.00,
        "fee_pct": 0.03,
        "fee_usd": 300.00  # Server computes: award_amount * fee_pct
    }
}
```

---

## Verification Checklist (Per App)

### Pre-Launch
- [ ] `APP_NAME` environment variable set
- [ ] `docs/system-prompts/universal.prompt` present
- [ ] Verification endpoint returns `architecture: "universal"`
- [ ] App overlay extracted successfully via `/api/prompts/overlay/{app_key}`

### Launch
- [ ] Bootstrap event `overlay_selected` emitted on first load
- [ ] All must-emit events instrumented per app overlay
- [ ] Revenue events include `revenue_usd` (B2C) or `fee_usd` (B2B)
- [ ] Headers propagated: `X-Request-ID`, `X-Session-ID`, `X-User-ID`

### Post-Launch (T+24h)
- [ ] Events appearing in `business_events` table
- [ ] Event volume >100/day (or baseline for app)
- [ ] P95 latency ≤120ms (check `/api/prompts/verify` + app metrics)
- [ ] No error rate increase

### Revenue Validation (T+48h)
- [ ] Query confirms revenue events:
  ```sql
  SELECT event_name, COUNT(*), 
         SUM(CAST(properties->>'revenue_usd' AS DECIMAL)) as total_revenue
  FROM business_events
  WHERE event_name IN ('credits_purchased', 'application_submitted', 'scholarship_posted')
  GROUP BY event_name;
  ```
- [ ] B2C: `credits_purchased.revenue_usd > 0`
- [ ] B2B: `scholarship_posted.fee_usd > 0`

---

## Troubleshooting

### Issue: Overlay Not Found
**Symptom:** `GET /api/prompts/overlay/{app_key}` returns 404

**Solution:**
1. Check `APP_NAME` matches exactly (case-sensitive): `scholar_auth`, `student_pilot`, etc.
2. Verify `universal.prompt` contains `[APP: {app_key}]` section
3. Fallback to individual file: `{app_key}.prompt`

### Issue: Events Not Appearing
**Symptom:** No rows in `business_events` table

**Solution:**
1. Check event emission service logs
2. Verify `business_events` table exists: `\dt business_events`
3. Check circuit breaker state (may be open after failures)
4. Manually emit test event and check logs

### Issue: Revenue Not Tracking
**Symptom:** `revenue_usd` or `fee_usd` is NULL or 0

**Solution:**
1. Verify event includes `properties.revenue_usd` (B2C) or `properties.fee_usd` (B2B)
2. Check server-side computation for `fee_usd = award_amount * 0.03`
3. Query database:
   ```sql
   SELECT properties FROM business_events 
   WHERE event_name = 'credits_purchased' 
   LIMIT 1;
   ```

---

## Success Metrics (T+72h)

### Event Coverage
- **Target:** ≥99% of must-emit events instrumented across all 8 apps
- **Measure:** `COUNT(DISTINCT event_name) / total_required_events`

### Revenue Visibility
- **B2C (Student Pilot):** First `credits_purchased.revenue_usd > 0`
- **B2B (Provider Register):** First `scholarship_posted.fee_usd > 0`
- **Dashboard:** Executive Command Center shows MRR/ARR in daily brief

### Performance
- **P95 Latency:** ≤120ms for all apps
- **Uptime:** ≥99.9% (no SLO breaches)
- **Error Rate:** <0.1% increase post-rollout

### KPI Reporting
- **Daily Brief:** Automated 09:00 UTC delivery
- **KPI Accuracy:** Real revenue data (not estimates)
- **Alert Coverage:** Anomaly detection operational

---

## Rollback Plan

If critical issues arise during rollout:

### Individual App Rollback
1. Remove `universal.prompt` or set `PROMPT_MODE=separate`
2. System auto-detects and falls back to `{app_key}.prompt`
3. No code changes required

### Full Ecosystem Rollback
1. Delete `docs/system-prompts/universal.prompt`
2. All apps revert to individual files automatically
3. Verification endpoint returns `architecture: "individual"`

**No data loss:** Events continue emitting to `business_events` regardless of prompt architecture

---

## Support & Escalation

### Documentation
- `docs/UNIVERSAL_PROMPT_GUIDE.md` - Architecture overview
- `docs/IMPLEMENTATION_GUIDE_FOR_APP_OWNERS.md` - Code examples
- `docs/BUSINESS_EVENTS_INSTRUMENTATION_GUIDE.md` - Event standards

### Debugging Endpoints
- `GET /api/prompts/verify` - Architecture and hash verification
- `GET /api/prompts/overlay/{app_key}` - View app-specific overlay
- `GET /api/prompts/merge/{app_key}` - View merged prompt

### Escalation Path
1. Check logs: `refresh_all_logs` tool
2. Verify database: Query `business_events` table
3. Emit `exception_escalated` event with context
4. Contact #engineering-kpis Slack channel

---

**Version:** 1.0.0  
**Owner:** ScholarshipAI Ecosystem Team  
**Deadline:** 72 hours from T+0 (October 28, 2025)  
**Status:** Phase 1 Complete (Scholarship API ✅)
