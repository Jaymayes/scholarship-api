# Per-App Quick Starts (Copy-Paste Ready)

**CEO Directive:** All teams must adopt Universal Prompt v1.1 within 72 hours.

Each app team can copy their section below and follow the steps to deploy.

---

## 1. Executive Command Center

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=executive_command_center
export APP_NAME="Executive Command Center"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "executive_command_center",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# KPI Brief (daily at 09:00 UTC)
await emit_business_event("kpi_brief_generated", {
    "arr_usd": 765432.10,              # Annual recurring revenue
    "b2c_arpu": 12.45,                 # Average revenue per user (B2C)
    "b2c_conv_rate": 0.08,             # Free → paid conversion rate
    "b2b_active_providers": 245,       # Active provider count
    "fee_revenue_usd": 8901.23,        # B2B fee revenue (24h)
    "cac": 15.67,                      # Customer acquisition cost
    "p95_ms": 95,                      # P95 latency
    "uptime": 0.9998                   # Uptime percentage
})
```

### Validation
```bash
# Verify prompt loaded
curl http://localhost:5000/api/prompts/verify | jq '.app'

# Verify overlay selected
grep "overlay_selected" /tmp/logs/*.log | tail -1

# Verify KPI brief
grep "kpi_brief_generated" /tmp/logs/*.log | tail -1
```

---

## 2. Auto Page Maker

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=auto_page_maker
export APP_NAME="Auto Page Maker"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "auto_page_maker",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# Page plan created
await emit_business_event("page_plan_created", {
    "topic": "STEM scholarships for women",
    "targets": ["undergrad", "graduate", "research"]
})

# Page published
await emit_business_event("page_published", {
    "url": "/scholarships/stem-women",
    "topic": "STEM scholarships for women"
})
```

### Validation
```bash
# Verify SEO pages created
grep "page_published" /tmp/logs/*.log | tail -5
```

---

## 3. Student Pilot (B2C Revenue) 🔥 REVENUE CRITICAL

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=student_pilot
export APP_NAME="Student Pilot"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "student_pilot",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# Credit purchase (REVENUE EVENT - CEO PRIORITY)
await emit_business_event("credit_purchase_succeeded", {
    "revenue_usd": 9.99,               # REQUIRED: Actual revenue
    "credits_purchased": 100,          # REQUIRED: Credit amount
    "sku": "starter_pack_100",         # REQUIRED: Product SKU
    "user_id_hash": user_id_hash       # Optional: Hashed user ID
})
```

### Validation
```sql
-- Verify B2C revenue tracking
SELECT 
    DATE(ts) as date,
    COUNT(*) as purchases,
    SUM((properties->>'revenue_usd')::float) as total_revenue,
    AVG((properties->>'revenue_usd')::float) as avg_revenue,
    SUM((properties->>'credits_purchased')::int) as total_credits
FROM business_events 
WHERE event_name = 'credit_purchase_succeeded'
GROUP BY DATE(ts)
ORDER BY date DESC;

-- Expected: Non-zero revenue within 24h of deployment
```

### Success Criteria
- ✅ `credit_purchase_succeeded` emitted on every purchase
- ✅ `revenue_usd` field always present
- ✅ No PII in event properties
- ✅ Revenue visible in KPI dashboard within 24h

---

## 4. Provider Register (B2B Revenue) 🔥 REVENUE CRITICAL

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=provider_register
export APP_NAME="Provider Register"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "provider_register",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# Provider onboarded
await emit_business_event("provider_onboarded", {
    "provider_id_hash": provider_id_hash
})

# Fee accrued (REVENUE EVENT - CEO PRIORITY)
# CRITICAL: fee_usd MUST be computed SERVER-SIDE ONLY!
fee_usd = award_amount * 0.03  # Backend calculation only!

await emit_business_event("fee_accrued", {
    "scholarship_id": scholarship_id,  # REQUIRED
    "fee_usd": fee_usd,                # REQUIRED (server-computed!)
    "award_amount": award_amount       # REQUIRED
})
```

### Validation
```sql
-- Verify B2B fee tracking
SELECT 
    scholarship_id,
    (properties->>'fee_usd')::float as fee_usd,
    (properties->>'award_amount')::float as award_amount,
    ABS((properties->>'fee_usd')::float - (properties->>'award_amount')::float * 0.03) as variance
FROM business_events 
WHERE event_name = 'fee_accrued'
ORDER BY ts DESC
LIMIT 10;

-- Expected: variance < $0.01 for all rows (server-side calculation correct)

-- Total B2B revenue
SELECT 
    DATE(ts) as date,
    COUNT(*) as fee_events,
    SUM((properties->>'fee_usd')::float) as total_fees,
    AVG((properties->>'award_amount')::float) as avg_award
FROM business_events 
WHERE event_name = 'fee_accrued'
GROUP BY DATE(ts)
ORDER BY date DESC;
```

### Success Criteria
- ✅ `fee_accrued` emitted when scholarship posted
- ✅ `fee_usd` calculated server-side (variance < $0.01)
- ✅ No client-side fee calculation
- ✅ B2B revenue visible in KPI dashboard within 24h

---

## 5. Scholarship API

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=scholarship_api
export APP_NAME="Scholarship API"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "scholarship_api",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# API doc viewed
await emit_business_event("api_doc_viewed", {
    "endpoint": "/api/v1/scholarships/search",
    "intent": "integration_guide"
})
```

### Validation
```bash
# Verify API docs tracking
grep "api_doc_viewed" /tmp/logs/*.log | tail -5
```

---

## 6. Scholarship Agent

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=scholarship_agent
export APP_NAME="Scholarship Agent"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "scholarship_agent",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# Experiment defined
await emit_business_event("experiment_defined", {
    "metric": "scholarship_view_to_save",
    "target": 0.15
})

# Campaign plan created
await emit_business_event("campaign_plan_created", {
    "channel": "email",
    "goal": "increase_applications"
})
```

### Validation
```bash
# Verify campaign tracking
grep "campaign_plan_created" /tmp/logs/*.log | tail -5
```

---

## 7. Scholar Auth

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=scholar_auth
export APP_NAME="Scholar Auth"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "scholar_auth",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# Auth doc viewed
await emit_business_event("auth_doc_viewed", {
    "flow": "oauth2_authorization_code",
    "intent": "integration"
})
```

### Validation
```bash
# Verify auth docs tracking
grep "auth_doc_viewed" /tmp/logs/*.log | tail -5
```

---

## 8. Scholarship Sage

### Configuration
```bash
export PROMPT_MODE=universal
export APP_OVERLAY=scholarship_sage
export APP_NAME="Scholarship Sage"
```

### Required Events
```python
from services.event_emission import emit_business_event

# Bootstrap (on app startup)
await emit_business_event("overlay_selected", {
    "app_key": "scholarship_sage",
    "detection_method": "env_var",
    "mode": "universal",
    "prompt_version": "1.1"
})

# Guidance provided
await emit_business_event("guidance_provided", {
    "topic": "eligibility_requirements",
    "depth": "detailed"
})
```

### Validation
```bash
# Verify guidance tracking
grep "guidance_provided" /tmp/logs/*.log | tail -5
```

---

## Universal Validation (All Apps)

### Bootstrap Event Check
```sql
-- Verify all apps emit overlay_selected on startup
SELECT 
    (properties->>'app_key') as app,
    (properties->>'detection_method') as method,
    COUNT(*) as sessions
FROM business_events 
WHERE event_name = 'overlay_selected'
GROUP BY app, method
ORDER BY sessions DESC;

-- Expected: 8 apps reporting
```

### PII Safety Check
```bash
# Scan for PII patterns (should return nothing)
grep -iE 'email|ssn|phone|password' /tmp/logs/*.log | grep -v "user_agent"
```

### SLO Check
```sql
-- Check for SLO violations
SELECT 
    ts,
    (properties->>'p95_ms')::float as p95,
    (properties->>'uptime')::float as uptime,
    properties->>'risk_reason' as reason
FROM business_events 
WHERE event_name = 'slo_at_risk'
ORDER BY ts DESC
LIMIT 10;

-- Expected: Zero or minimal slo_at_risk events
```

---

## Rollout Timeline

### T+0 (October 28) ✅ COMPLETE
- ✅ Scholarship API deployed

### T+24h (October 29) 📅 NEXT
- 🎯 Scholarship Agent
- 🎯 Auto Page Maker

### T+48h (October 30) 🔥 REVENUE CRITICAL
- 🎯 Student Pilot (B2C revenue)
- 🎯 Provider Register (B2B revenue)

### T+72h (October 31) 🎯 CEO DEADLINE
- 🎯 Executive Command Center
- 🎯 Scholar Auth
- 🎯 Scholarship Sage

**Success:** First `kpi_brief_generated` with non-zero `arr_usd` and `fee_revenue_usd`

---

## Instant Rollback

If issues arise, revert immediately:

```bash
export PROMPT_MODE=separate
# No code changes required - system uses individual prompts
```

---

## Support Resources

- **Universal Prompt:** `docs/system-prompts/universal.prompt`
- **Team Instructions:** `docs/UNIVERSAL_PROMPT_TEAM_INSTRUCTIONS.md`
- **Event Guide:** `docs/BUSINESS_EVENTS_INSTRUMENTATION_GUIDE.md`
- **SQL Validation:** `docs/SQL_VALIDATION_PACK.md`

---

**Questions?** Check logs, verify events, run SQL queries above. All apps must be live by T+72h.
