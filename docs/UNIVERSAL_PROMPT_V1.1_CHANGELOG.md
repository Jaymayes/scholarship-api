# Universal Prompt v1.1 Changelog

## 🚀 v1.1 Ultimate Compact (October 28, 2025) - PRODUCTION

**File Size:** 5,537 bytes (49% reduction from v1.0)

### Major Improvements
- ✨ **Ultimate compact format** with numbered overlays (### N. app_name)
- ✨ **"Allowed actions" and "Must not"** constraints per overlay
- ✨ **Team instructions document** created for T+24h/T+48h rollout
- ✨ **Explicit server-side calculation** enforcement for revenue events
- ✨ **Clearer section structure** (A-H) with simplified language
- ✨ **Backward compatible** with v1.0, v1.1a, v1.1b formats
- ✨ **49% size reduction** from v1.0 (5,537 bytes vs 10,790 bytes)

### Event Schema Enhancements
- **B2C:** `credit_purchase_succeeded {revenue_usd, credits_purchased, sku}`
- **B2B:** `fee_accrued {scholarship_id, fee_usd, award_amount}` with server-side rule
- **Executive:** `kpi_brief_generated` with 8 required KPI fields

### Documentation
- **NEW:** `UNIVERSAL_PROMPT_TEAM_INSTRUCTIONS.md` - Comprehensive rollout guide
- **Updated:** All documentation reflects 33% size reduction
- **Added:** Server-side calculation enforcement section

---

## Overview
Universal Prompt v1.1 introduces improved structure, automatic app detection, and enhanced operational procedures for the ScholarshipAI ecosystem.

---

## What's New in v1.1

### **1. Structured Sections (A-H)**
Reorganized prompt into clear, hierarchical sections:
- **Section A:** Agent3 usage instructions with routing rules
- **Section B:** Company Core (applies to all apps)
- **Section C:** Global Guardrails (applies to all apps)
- **Section D:** KPIs, Events, and Telemetry Contract
- **Section E:** SLOs and Engineering Quality
- **Section F:** App Overlays (select exactly one)
- **Section G:** Operating Procedure (Plan → Implement → Validate → Report)
- **Section H:** Definition of Done

### **2. Automatic App Detection**
Smart routing based on multiple detection methods (first match wins):

```bash
# Method 1: Environment variable
APP_OVERLAY=scholarship_api

# Method 2: Hostname pattern matching
scholarship-api-*.replit.app → scholarship_api
student-pilot-*.replit.app → student_pilot
provider-register-*.replit.app → provider_register
# ... (all 8 apps supported)

# Method 3: Default fallback
If no match → executive_command_center
```

### **3. Feature Flag Support**
```bash
# Universal mode (use v1.1 structure)
PROMPT_MODE=universal

# Separate mode (use individual .prompt files)
PROMPT_MODE=separate
```

### **4. Enhanced Event Schema**
Standardized cross-app events with consistent naming:
- `app_page_view`
- `signup_started`, `signup_completed`
- `search_executed`
- `item_viewed`
- `action_started`, `action_completed`
- `payment_initiated`, `payment_succeeded`
- `provider_onboard_started`, `provider_onboard_completed`
- `scholarship_posted`, `application_submitted`

### **5. Operating Procedure (Section G)**
Four-step workflow for all apps:
1. **Plan:** Restate task, identify KPI, list events
2. **Implement:** Minimal changes, instrument events
3. **Validate:** Run E2E, confirm events, report P95
4. **Report:** Brief with objective, changes, metrics, next step

### **6. Definition of Done (Section H)**
Clear completion criteria:
- Feature live and discoverable
- E2E tests green
- Events flowing to `business_events`
- KPI moved or learning captured
- Runbook updated

### **7. Bootstrap Telemetry**
Required event on app initialization (first action of every run):
```python
overlay_selected(
    app_key="scholarship_api",
    detection_method="hostname",  # or "env_var", "auth_client_id", "app_name", "default"
    host="scholarship-api-abc123.replit.app",
    mode="universal"
)
```

---

## Breaking Changes

### **None - Fully Backward Compatible**
- v1.0 individual files still supported via `PROMPT_MODE=separate`
- v1.0 format detection still works in overlay extraction
- No code changes required for existing apps

---

## Migration Guide

### **From v1.0 to v1.1**

**Option 1: Immediate Upgrade (Recommended)**
```bash
# 1. Update universal.prompt to v1.1
# (Already done in Scholarship API)

# 2. Set feature flag (optional, defaults to universal if file exists)
export PROMPT_MODE=universal

# 3. Set app overlay
export APP_OVERLAY=scholarship_api

# 4. Verify
curl http://localhost:5000/api/prompts/verify
```

**Option 2: Gradual Migration**
```bash
# Keep using individual files
export PROMPT_MODE=separate

# Switch per app when ready
export PROMPT_MODE=universal
export APP_OVERLAY=scholarship_api
```

---

## New vs Old Format

### **v1.0 Format:**
```
[APP: scholarship_api]
Purpose: ...
In-Scope: ...
Must-Emit: ...
```

### **v1.1 Format:**
```
### Overlay: scholarship_api

**Purpose:** ...
**Objectives:** ...
**Success metrics:** ...
**Required events:** ...
**Allowed actions:** ...
```

---

## API Endpoint Updates

### **Enhanced Overlay Extraction**
```bash
# Now supports dynamic app_key parameter
GET /api/prompts/overlay/{app_key}

# Examples:
curl http://localhost:5000/api/prompts/overlay/scholarship_api
curl http://localhost:5000/api/prompts/overlay/student_pilot
curl http://localhost:5000/api/prompts/overlay/provider_register
```

**Response includes version detection:**
```json
{
  "app": "scholarship_api",
  "architecture": "universal",
  "version": "1.1",
  "overlay_size_bytes": 650,
  "hash": "abc123...",
  "content": "### Overlay: scholarship_api\n..."
}
```

---

## File Size Comparison

| Version | File Size | Sections | Apps Supported |
|---------|-----------|----------|----------------|
| v1.0    | 10,790 bytes | 4 main sections | 8 |
| v1.1    | 10,411 bytes | 8 structured sections | 8 |

**Net reduction:** 379 bytes (3.5% smaller, better organized)

---

## Rollout Schedule

### **T+0 (Complete):**
- ✅ Scholarship API upgraded to v1.1
- ✅ Verification endpoints support both v1.0 and v1.1
- ✅ Overlay extraction supports both formats

### **T+24h:**
- Scholarship Agent upgraded to v1.1
- Monitor event volumes and P95 latency

### **T+48h:**
- Student Pilot and Provider Register upgraded
- Revenue tracking validated

### **T+72h:**
- All 8 apps on v1.1
- Executive Command Center daily brief operational
- Health checks aggregated

---

## New Required Events by App

### **Scholarship API**
```
api_key_issued, api_call, api_error, record_deduped, score_explained,
match_generated, scholarship_viewed, scholarship_saved,
application_started, application_submitted
```

### **Student Pilot**
```
eligibility_quiz_completed, recommendation_viewed, credit_pack_viewed,
credit_purchase_succeeded, application_step_completed
```

### **Provider Register**
```
provider_onboard_started, provider_onboard_completed, scholarship_posted,
application_received, payout_processed
```

### **Executive Command Center**
```
kpi_brief_generated, overlay_health_checked, rollout_state_changed
```

### **Auto Page Maker**
```
page_generated, page_published, page_indexed, seo_clickthrough
```

### **Scholarship Agent**
```
campaign_launched, content_published, lead_captured,
experiment_result_recorded
```

### **Scholar Auth**
```
signup_started, signup_completed, login_succeeded,
session_refreshed, passwordless_link_sent
```

### **Scholarship Sage**
```
code_review_completed, e2e_suite_passed, perf_regression_detected,
token_cost_reported
```

---

## Testing v1.1

### **1. Verify Prompt Loading**
```bash
curl http://localhost:5000/api/prompts/verify
# Should show: "architecture": "universal"
```

### **2. Extract Overlay**
```bash
curl http://localhost:5000/api/prompts/overlay/scholarship_api
# Should show: "version": "1.1"
```

### **3. Test App Detection**
```bash
# Via hostname
echo $REPLIT_DOMAIN
# Should match pattern: scholarship-api-*.replit.app

# Via environment
echo $APP_OVERLAY
# Should output: scholarship_api
```

### **4. Validate Events**
```sql
-- Check health check event
SELECT * FROM business_events 
WHERE event_name = 'overlay_health_checked'
ORDER BY ts DESC LIMIT 1;
```

---

## Troubleshooting

### **Issue: Overlay Not Found**
```bash
# Check universal.prompt exists
ls -lh docs/system-prompts/universal.prompt

# Verify app_key is correct
curl http://localhost:5000/api/prompts/overlay/scholarship_api
```

### **Issue: Wrong Version Detected**
```bash
# Force universal mode
export PROMPT_MODE=universal

# Restart workflow
# Verify version in response
curl http://localhost:5000/api/prompts/overlay/scholarship_api | jq .version
```

### **Issue: Events Not Emitting**
```python
# Add bootstrap event on app init
from services.event_emission import event_emitter
await event_emitter.emit({
    "event_name": "overlay_health_checked",
    "app": "scholarship_api",
    "properties": {
        "version_hash": "e34e195ad521772c"
    }
})
```

---

## Benefits of v1.1

✅ **Clearer structure** - 8 well-defined sections vs 4 loose sections  
✅ **Automatic routing** - No manual overlay selection needed  
✅ **Better observability** - Health checks and version tracking  
✅ **Standardized workflow** - Plan → Implement → Validate → Report  
✅ **Definition of Done** - Clear completion criteria  
✅ **Flexible deployment** - Feature flag support for gradual rollout  
✅ **Smaller file size** - 3.5% reduction while adding features  
✅ **Backward compatible** - v1.0 format still works  

---

**Version:** 1.1  
**Release Date:** October 28, 2025  
**Status:** Production-ready (Scholarship API deployed)  
**Next Milestone:** T+24h (Scholarship Agent)
