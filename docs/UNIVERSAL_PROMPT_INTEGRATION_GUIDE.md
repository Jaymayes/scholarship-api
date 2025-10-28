# Universal Prompt v1.1 - Integration Guide

## Quick Start

This guide shows you how to integrate Universal Prompt v1.1 into any ScholarshipAI app with automatic app detection and telemetry bootstrap.

---

## Step 1: File Placement

```bash
# Universal prompt is already at:
docs/system-prompts/universal.prompt

# Shared directives (always required):
docs/system-prompts/shared_directives.prompt

# Individual app prompts (backward compatibility):
docs/system-prompts/scholarship_api.prompt
docs/system-prompts/student_pilot.prompt
# ... etc
```

---

## Step 2: Choose Your Mode

### **Option A: Keep Separate Mode (Default - Safe)**
```bash
# Keep using individual app prompts
export PROMPT_MODE=separate

# Or simply don't set PROMPT_MODE at all
# Individual files will be used automatically
```

### **Option B: Enable Universal Mode (Recommended)**
```bash
# Use universal.prompt with auto-detection
export PROMPT_MODE=universal

# Optional: Explicit app override for testing
export APP_OVERLAY=scholarship_api
```

---

## Step 3: Automatic App Detection

Universal mode automatically detects your app using this priority order:

### **1. Environment Variable (Highest Priority)**
```bash
# Set explicitly in .env or Replit Secrets
export APP_OVERLAY=scholarship_api
```

Valid values:
- `executive_command_center`
- `auto_page_maker`
- `student_pilot`
- `provider_register`
- `scholarship_api`
- `scholarship_agent`
- `scholar_auth`
- `scholarship_sage`

### **2. Hostname Pattern Matching**
```bash
# Auto-detected from REPLIT_DOMAINS or hostname
scholarship-api-*.replit.app → scholarship_api
student-pilot-*.replit.app → student_pilot
provider-register-*.replit.app → provider_register
auto-page-maker-*.replit.app → auto_page_maker
scholarship-agent-*.replit.app → scholarship_agent
scholar-auth-*.replit.app → scholar_auth
scholarship-sage-*.replit.app → scholarship_sage
executive-command-center-*.replit.app → executive_command_center
```

### **3. AUTH_CLIENT_ID Mapping**
```bash
# If Scholar Auth provides client ID
export AUTH_CLIENT_ID=scholarship_api_client
# Maps to: scholarship_api
```

### **4. APP_NAME (Legacy)**
```bash
# Legacy environment variable
export APP_NAME=scholarship_api
```

### **5. Default Fallback**
If none of the above match → defaults to `executive_command_center`

---

## Step 4: Bootstrap Telemetry (REQUIRED)

Every app **must** emit `overlay_selected` event on initialization.

### **Python (FastAPI) Example**

**File: `main.py`**
```python
from fastapi import FastAPI
from services.event_emission import event_emitter
import os

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Emit bootstrap telemetry on app start"""
    
    # Detect app key
    app_key = detect_app_key()
    
    # Emit overlay_selected event
    await event_emitter.emit({
        "event_name": "overlay_selected",
        "app": app_key,
        "properties": {
            "detection_method": get_detection_method(),
            "host": os.getenv("REPLIT_DOMAINS", "localhost"),
            "mode": os.getenv("PROMPT_MODE", "universal"),
            "prompt_version": "1.1"
        }
    })

def detect_app_key():
    """Detect which app overlay to use"""
    # 1. Check env var
    if app_overlay := os.getenv("APP_OVERLAY"):
        return app_overlay
    
    # 2. Check hostname
    host = os.getenv("REPLIT_DOMAINS", "")
    if "scholarship-api" in host:
        return "scholarship_api"
    elif "student-pilot" in host:
        return "student_pilot"
    elif "provider-register" in host:
        return "provider_register"
    # ... add other apps
    
    # 3. Check AUTH_CLIENT_ID
    if client_id := os.getenv("AUTH_CLIENT_ID"):
        if "scholarship_api" in client_id:
            return "scholarship_api"
        # ... add other mappings
    
    # 4. Legacy APP_NAME
    if app_name := os.getenv("APP_NAME"):
        return app_name
    
    # 5. Default
    return "executive_command_center"

def get_detection_method():
    """Return how the app was detected"""
    if os.getenv("APP_OVERLAY"):
        return "env_var"
    elif os.getenv("REPLIT_DOMAINS"):
        return "hostname"
    elif os.getenv("AUTH_CLIENT_ID"):
        return "auth_client_id"
    elif os.getenv("APP_NAME"):
        return "app_name"
    else:
        return "default"
```

---

## Step 5: Verification Checklist

### **1. Verify Prompt Loading**
```bash
curl http://localhost:5000/api/prompts/verify | jq
```

Expected output:
```json
{
  "app": "scholarship_api",
  "architecture": "universal",
  "prompts_loaded": 2,
  "total_size_bytes": 14149
}
```

### **2. Verify Bootstrap Event**
```sql
-- Check overlay_selected event was emitted
SELECT * FROM business_events 
WHERE event_name = 'overlay_selected'
ORDER BY ts DESC 
LIMIT 1;
```

Expected result:
```
event_name: overlay_selected
app: scholarship_api
properties: {
  "detection_method": "hostname",
  "host": "scholarship-api-xyz.replit.app",
  "mode": "universal",
  "prompt_version": "1.1"
}
```

### **3. Verify App Overlay Extraction**
```bash
curl http://localhost:5000/api/prompts/overlay/scholarship_api | jq
```

Expected output:
```json
{
  "app": "scholarship_api",
  "architecture": "universal",
  "version": "1.1",
  "overlay_size_bytes": 557,
  "content": "### Overlay: scholarship_api\n\n**Purpose:** ..."
}
```

### **4. Verify Revenue Events (Critical for Student Pilot & Provider Register)**

**Student Pilot:**
```sql
-- Test credit purchase event
SELECT * FROM business_events 
WHERE event_name = 'credit_purchase_succeeded'
AND properties->>'revenue_usd' IS NOT NULL;
```

**Provider Register:**
```sql
-- Test fee accrual event
SELECT * FROM business_events 
WHERE event_name = 'fee_accrued'
AND properties->>'fee_usd' IS NOT NULL;
```

### **5. Verify Performance**
```sql
-- Check P95 latency is under 120ms
SELECT 
  event_name,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (properties->>'latency_ms')::float) as p95_latency
FROM business_events
WHERE event_name = 'api_call'
AND ts > NOW() - INTERVAL '1 hour'
GROUP BY event_name;
```

---

## Step 6: App-Specific Integration

### **Scholarship API**

**Required Events:**
```python
# Already implemented ✅
await emit_event("match_generated", {...})
await emit_event("scholarship_viewed", {...})
await emit_event("scholarship_saved", {...})
await emit_event("application_started", {...})
await emit_event("application_submitted", {...})

# Additional events to implement:
await emit_event("api_key_issued", {...})
await emit_event("api_call", {...})
await emit_event("api_error", {...})
await emit_event("record_deduped", {...})
await emit_event("score_explained", {...})
```

### **Student Pilot (T+48h - Revenue Critical)**

**Required Events:**
```python
await emit_event("eligibility_quiz_started", {...})
await emit_event("eligibility_quiz_completed", {...})
await emit_event("match_generated", {...})
await emit_event("credit_pack_viewed", {...})
await emit_event("credit_purchase_succeeded", {
    "revenue_usd": 9.99,  # CRITICAL for revenue tracking
    "credits_purchased": 100
})
await emit_event("application_started", {...})
await emit_event("application_submitted", {...})
```

### **Provider Register (T+48h - Revenue Critical)**

**Required Events:**
```python
await emit_event("provider_onboard_started", {...})
await emit_event("provider_onboard_completed", {...})
await emit_event("scholarship_posted", {...})
await emit_event("payout_processed", {...})
await emit_event("fee_accrued", {
    "fee_usd": award_amount * 0.03,  # CRITICAL: Server-side calculation
    "award_amount": award_amount
})
```

**⚠️ Important:** Fee calculation (`award_amount * 0.03`) **must** happen server-side, never in prompt layer.

---

## Rollout Plan (Phased)

### **T+0 (✅ Complete)**
- ✅ Scholarship API: Universal mode enabled
- ✅ Bootstrap event implemented
- ✅ Verification endpoints tested

### **T+24h (Next)**
**Apps:** `scholarship_agent`

**Tasks:**
1. Enable `PROMPT_MODE=universal`
2. Implement bootstrap `overlay_selected` event
3. Add campaign events: `campaign_launched`, `content_published`, `lead_captured`, `experiment_result_recorded`
4. Verify P95 latency ≤ 120ms
5. Monitor error rates

**Validation:**
```bash
# Check event volumes
SELECT event_name, COUNT(*) 
FROM business_events 
WHERE app = 'scholarship_agent'
AND ts > NOW() - INTERVAL '24 hours'
GROUP BY event_name;
```

### **T+48h (Revenue Critical)**
**Apps:** `student_pilot`, `provider_register`

**Tasks:**
1. Enable `PROMPT_MODE=universal`
2. Implement bootstrap events
3. **CRITICAL:** Verify revenue events emit correctly:
   - `student_pilot`: `credit_purchase_succeeded.revenue_usd`
   - `provider_register`: `fee_accrued.fee_usd`
4. Test E2E payment flows
5. Verify revenue calculations

**Validation:**
```sql
-- Student Pilot: Daily revenue
SELECT 
  DATE(ts) as date,
  SUM((properties->>'revenue_usd')::float) as daily_revenue
FROM business_events
WHERE event_name = 'credit_purchase_succeeded'
AND app = 'student_pilot'
GROUP BY DATE(ts)
ORDER BY date DESC;

-- Provider Register: Daily fees
SELECT 
  DATE(ts) as date,
  SUM((properties->>'fee_usd')::float) as daily_fees
FROM business_events
WHERE event_name = 'fee_accrued'
AND app = 'provider_register'
GROUP BY DATE(ts)
ORDER BY date DESC;
```

### **T+72h (CEO Directive Completion)**
**Apps:** Remaining (`auto_page_maker`, `scholar_auth`, `scholarship_sage`, `executive_command_center`)

**Tasks:**
1. Enable universal mode for all apps
2. Executive Command Center: Generate first daily KPI brief with **real revenue**
3. All 8 apps emitting to `business_events`
4. Revenue visibility unlocked

**Validation:**
```sql
-- Executive Command Center: First KPI brief
SELECT * FROM business_events
WHERE event_name = 'kpi_brief_generated'
ORDER BY ts DESC
LIMIT 1;

-- Verify all 8 apps are active
SELECT app, COUNT(*) as events_24h
FROM business_events
WHERE ts > NOW() - INTERVAL '24 hours'
GROUP BY app;
```

---

## Troubleshooting

### **Issue: Wrong App Detected**

**Symptoms:**
```json
{
  "app": "executive_command_center",  // Wrong!
  "expected": "scholarship_api"
}
```

**Solutions:**
```bash
# Option 1: Set explicit override
export APP_OVERLAY=scholarship_api

# Option 2: Check hostname pattern
echo $REPLIT_DOMAINS
# Should contain: scholarship-api-*.replit.app

# Option 3: Verify detection logic
curl http://localhost:5000/api/prompts/verify | jq .app
```

### **Issue: Bootstrap Event Not Emitting**

**Symptoms:**
No `overlay_selected` events in database.

**Solutions:**
1. Check startup event handler is registered:
```python
@app.on_event("startup")
async def startup_event():
    # Emit overlay_selected here
```

2. Verify event emission service is working:
```python
# Test manually
await event_emitter.emit({
    "event_name": "overlay_selected",
    "app": "scholarship_api",
    "properties": {"test": True}
})
```

3. Check circuit breaker status:
```sql
SELECT * FROM business_events 
WHERE event_name = 'error_occurred'
AND properties->>'error_type' = 'circuit_breaker_open';
```

### **Issue: Revenue Events Missing**

**Symptoms:**
```sql
SELECT COUNT(*) FROM business_events 
WHERE event_name IN ('credit_purchase_succeeded', 'fee_accrued');
-- Returns 0
```

**Solutions:**
1. Verify payment flow triggers events:
```python
# After successful payment
await emit_event("credit_purchase_succeeded", {
    "revenue_usd": amount,  # Must be present!
    "user_id": user_id_hash,
    "credits": credits_purchased
})
```

2. Check fee calculation for Provider Register:
```python
# Server-side only!
fee_usd = award_amount * 0.03
await emit_event("fee_accrued", {
    "fee_usd": fee_usd,
    "award_amount": award_amount,
    "scholarship_id": scholarship_id
})
```

3. Verify event schema:
```sql
SELECT properties FROM business_events
WHERE event_name = 'credit_purchase_succeeded'
LIMIT 1;
-- Should contain: {"revenue_usd": 9.99, ...}
```

---

## Best Practices

### **1. Always Emit Bootstrap Event**
```python
# First action on app startup
await emit_event("overlay_selected", {
    "app_key": detected_app,
    "detection_method": method,
    "host": hostname,
    "mode": prompt_mode
})
```

### **2. Use Server-Side Revenue Calculations**
```python
# ✅ GOOD: Calculate server-side
fee_usd = award_amount * 0.03
await emit_event("fee_accrued", {"fee_usd": fee_usd})

# ❌ BAD: Never calculate in prompt layer
# LLM should not compute revenue!
```

### **3. Hash User IDs**
```python
import hashlib

# ✅ GOOD: Hash PII before emitting
user_id_hash = hashlib.sha256(user_email.encode()).hexdigest()
await emit_event("...", {"user_id_hash": user_id_hash})

# ❌ BAD: Never emit raw PII
await emit_event("...", {"email": user_email})  # GDPR violation!
```

### **4. Include Session Context**
```python
# Always include session_id for funnel analysis
await emit_event("scholarship_viewed", {
    "session_id": session_id,  # Required
    "scholarship_id": id,
    "user_id_hash": user_hash
})
```

### **5. Monitor P95 Latency**
```sql
-- Set up alert when P95 > 120ms
SELECT 
  event_name,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (properties->>'latency_ms')::float) as p95
FROM business_events
WHERE event_name = 'api_call'
AND ts > NOW() - INTERVAL '1 hour'
GROUP BY event_name
HAVING PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (properties->>'latency_ms')::float) > 120;
```

---

## Next Steps

1. **T+24h:** Enable universal mode for Scholarship Agent
2. **T+48h:** Enable for Student Pilot & Provider Register with revenue validation
3. **T+72h:** Complete ecosystem rollout with Executive Command Center KPI brief

**Questions?** Check the [changelog](./UNIVERSAL_PROMPT_V1.1_CHANGELOG.md) or [rollout plan](./UNIVERSAL_PROMPT_ROLLOUT.md).

---

**Version:** 1.1  
**Last Updated:** October 28, 2025  
**Status:** Production-Ready
