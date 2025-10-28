# Universal Prompt v1.1 - Team Instructions

## 🎯 Quick Start

**File Location:** `docs/system-prompts/universal.prompt`

**Mode Configuration:**
```bash
# Enable universal mode (recommended for new apps)
export PROMPT_MODE=universal

# Or fallback to separate mode (legacy compatibility)
export PROMPT_MODE=separate
```

---

## 🔑 App Detection (Preferred Order)

Agent3 automatically detects which app overlay to use based on this priority:

1. **`APP_OVERLAY` env var** (explicit override)
   ```bash
   export APP_OVERLAY=student_pilot
   ```

2. **Hostname pattern matching**
   ```
   student-pilot-*.replit.app     → student_pilot
   provider-register-*.replit.app → provider_register
   scholarship-api-*.replit.app   → scholarship_api
   ```

3. **Request path or header `app_key`**
   ```
   X-App-Key: scholarship_agent
   ```

4. **Fallback to explicit parameter**
   ```python
   overlay = request.query_params.get("app_overlay", "executive_command_center")
   ```

---

## 📊 Bootstrap Event (MANDATORY)

**Every app startup must emit `overlay_selected` event:**

```python
from services.event_emission import emit_event

# First action on app initialization
await emit_event("overlay_selected", {
    "app_key": "student_pilot",              # Your app's overlay key
    "detection_method": "hostname",           # How app was detected
    "host": "student-pilot-xyz.replit.app",  # Current hostname
    "mode": "universal",                      # universal or separate
    "prompt_version": "1.1"                   # Prompt version
})
```

---

## 🚨 Critical Server-Side Rule

**NEVER compute revenue calculations in Agent3 prompts or client-side:**

### ❌ WRONG (will cause audit failures)
```python
# In Agent3 prompt or client code - FORBIDDEN
fee_usd = award_amount * 0.03
```

### ✅ CORRECT (server-side only)
```python
# In your Python/Node backend service
fee_usd = award_amount * 0.03  # Server computes fee

await emit_event("fee_accrued", {
    "scholarship_id": scholarship_id,
    "fee_usd": fee_usd,          # Server-computed value
    "award_amount": award_amount
})
```

---

## 🎯 Required Events by App

### 1. executive_command_center
```python
kpi_brief_generated {
    arr_usd, b2c_arpu, b2c_conv_rate, 
    b2b_active_providers, fee_revenue_usd, 
    cac, p95_ms, uptime
}
overlay_health_checked {overlays_ok, anomalies}
rollout_state_changed {app_key, mode, previous_mode}
```

### 2. auto_page_maker
```python
content_brief_generated {topic, intent, eeat_checks}
content_published {url, word_count, eeat_passed, schema_markup}
indexation_observed {url, indexed}
```

### 3. student_pilot (B2C Revenue) 🔥
```python
eligibility_quiz_started/completed {result_summary}
match_generated {count, top_score_explained}
credit_pack_viewed {sku}
credit_purchase_succeeded {revenue_usd, credits_purchased, sku}  # REVENUE
application_started/submitted {scholarship_id}
```

### 4. provider_register (B2B Revenue) 🔥
```python
provider_onboard_started/completed {provider_tier}
scholarship_posted {scholarship_id, award_amount}
fee_accrued {scholarship_id, fee_usd, award_amount}  # REVENUE (server-side!)
payout_processed {scholarship_id, payout_usd}
```

### 5. scholarship_api
```python
api_query_received {filters, rate_limit_bucket}
api_result_served {count, p95_ms, explanation_present}
api_rate_limited {bucket}
```

### 6. scholarship_agent
```python
campaign_launched {channel, hypothesis}
content_published {url, campaign_id}
lead_captured {lead_quality_score}
experiment_result_recorded {variant, uplift_pct}
attribution_recorded {campaign_id, assisted_revenue_usd}
```

### 7. scholar_auth
```python
signup_started/completed {method, mfa_enrolled}
login_succeeded/failed {reason_code}
password_reset_initiated/completed {}
```

### 8. scholarship_sage
```python
review_suite_run {suite_name, failures}
defect_logged {severity}
remediation_proposed {area, expected_impact}
```

---

## 🔒 Privacy & Compliance Rules

### Never include PII in event properties:
```python
# ❌ WRONG - contains PII
await emit_event("signup_completed", {
    "email": "student@example.com",      # PII - FORBIDDEN
    "name": "John Doe"                   # PII - FORBIDDEN
})

# ✅ CORRECT - PII hashed
import hashlib

user_id_hash = hashlib.sha256(user_email.encode()).hexdigest()

await emit_event("signup_completed", {
    "user_id_hash": user_id_hash,        # Hashed - OK
    "method": "email",
    "mfa_enrolled": True
})
```

---

## 📏 SLO Requirements

All apps must meet these targets:

| SLO | Target | Escalation Threshold |
|-----|--------|---------------------|
| **Uptime** | ≥ 99.9% | < 99.5% for 1 hour |
| **P95 Latency** | ≤ 120ms | > 150ms for 5 minutes |
| **Event Drop Rate** | < 1% | > 10% for 15 minutes |
| **Revenue Event Completeness** | 100% | Any missing required fields |

---

## 🚀 Rollout Timeline (CEO Directive)

### T+0 (October 28, 2025) ✅ COMPLETE
- ✅ Scholarship API fully operational
- ✅ Universal Prompt v1.1 deployed
- ✅ All verification endpoints passing

### T+24h (October 29, 2025) 📅 NEXT
**Target Apps:** scholarship_agent, auto_page_maker

**Implementation Checklist:**
```bash
# 1. Enable universal mode
export PROMPT_MODE=universal
export APP_OVERLAY=scholarship_agent

# 2. Implement bootstrap event (see code example above)

# 3. Implement required events
# scholarship_agent: 5 events
# auto_page_maker: 3 events

# 4. Verify metrics
curl http://localhost:5000/api/prompts/verify
```

**Success Criteria:**
- [ ] `overlay_selected` emitting on startup
- [ ] All required events flowing to `business_events` table
- [ ] P95 latency ≤ 120ms
- [ ] Zero PII in event properties

### T+48h (October 30, 2025) 🔥 REVENUE CRITICAL
**Target Apps:** student_pilot, provider_register

**Critical Revenue Events:**

**Student Pilot (B2C):**
```python
# Required for CEO KPI dashboard
await emit_event("credit_purchase_succeeded", {
    "revenue_usd": 9.99,          # REQUIRED
    "credits_purchased": 100,      # REQUIRED
    "sku": "starter_pack_100"      # REQUIRED
})
```

**Provider Register (B2B):**
```python
# Server-side calculation MANDATORY
fee_usd = award_amount * 0.03  # Compute in backend only!

await emit_event("fee_accrued", {
    "scholarship_id": scholarship_id,  # REQUIRED
    "fee_usd": fee_usd,                # REQUIRED (server-computed!)
    "award_amount": award_amount       # REQUIRED
})
```

**Validation Queries:**
```sql
-- Verify B2C revenue is tracking
SELECT 
  DATE(ts) as date,
  SUM((properties->>'revenue_usd')::float) as daily_revenue,
  COUNT(*) as purchases
FROM business_events 
WHERE event_name = 'credit_purchase_succeeded'
  AND app = 'student_pilot'
GROUP BY DATE(ts)
ORDER BY date DESC;

-- Verify B2B fee revenue is tracking
SELECT 
  DATE(ts) as date,
  SUM((properties->>'fee_usd')::float) as daily_fees,
  COUNT(*) as scholarships_posted
FROM business_events 
WHERE event_name = 'fee_accrued'
  AND app = 'provider_register'
GROUP BY DATE(ts)
ORDER BY date DESC;
```

### T+72h (October 31, 2025) 🎯 CEO DEADLINE
**Target:** Executive Command Center daily KPI brief with **real revenue**

**Required:**
```python
await emit_event("kpi_brief_generated", {
    "arr_usd": 765432.10,              # Real ARR from all sources
    "b2c_arpu": 12.45,                 # From student_pilot
    "b2c_conv_rate": 0.08,             # Free → paid conversion
    "b2b_active_providers": 245,       # From provider_register
    "fee_revenue_usd": 8901.23,        # From fee_accrued events
    "cac": 15.67,                      # Customer acquisition cost
    "p95_ms": 95,                      # System performance
    "uptime": 0.9998                   # System reliability
})
```

---

## 🧪 Testing Your Implementation

### 1. Verify Prompt Loading
```bash
curl http://localhost:5000/api/prompts/verify | jq
```

Expected output:
```json
{
  "prompts_loaded": 2,
  "architecture": "universal",
  "total_size_bytes": 12405
}
```

### 2. Extract Your App Overlay
```bash
curl http://localhost:5000/api/prompts/overlay/student_pilot | jq
```

Expected output includes your app's required events and allowed actions.

### 3. Verify Bootstrap Event
```sql
SELECT * FROM business_events 
WHERE event_name = 'overlay_selected' 
  AND app = 'student_pilot'
ORDER BY ts DESC 
LIMIT 5;
```

### 4. Check Event Completeness
```sql
-- Check for missing required fields
SELECT 
  event_name,
  COUNT(*) as total_events,
  COUNT(*) FILTER (WHERE properties->>'revenue_usd' IS NULL) as missing_revenue
FROM business_events
WHERE app = 'student_pilot'
  AND event_name = 'credit_purchase_succeeded'
GROUP BY event_name;
```

---

## 🆘 Troubleshooting

### Problem: Overlay not detected
**Solution:** Check detection order. Set explicit `APP_OVERLAY` env var:
```bash
export APP_OVERLAY=your_app_name
```

### Problem: Revenue events missing fields
**Solution:** Verify you're emitting all required fields per overlay definition.

### Problem: P95 latency > 120ms
**Solution:** 
1. Check database query performance
2. Review slow endpoints with profiling
3. Consider caching frequently accessed data
4. Escalate to executive_command_center

### Problem: PII detected in events
**Solution:**
```python
# Hash all user identifiers
import hashlib
user_id_hash = hashlib.sha256(user_email.encode()).hexdigest()

# Use hashed version in events
await emit_event("event_name", {
    "user_id_hash": user_id_hash,  # OK
    # Never include: email, name, phone, address
})
```

---

## 📞 Support

**Questions about Universal Prompt implementation:**
- Review: `docs/UNIVERSAL_PROMPT_INTEGRATION_GUIDE.md`
- Check: `docs/BUSINESS_EVENTS_INSTRUMENTATION_GUIDE.md`

**Revenue event validation:**
- Contact: Executive Command Center team
- Validate: Run SQL queries above before T+72h deadline

**Architecture questions:**
- Review: `docs/UNIVERSAL_PROMPT_V1.1_SUMMARY.md`

---

**Last Updated:** October 28, 2025  
**Version:** 1.1 (Final Compact)  
**Status:** Production-ready
