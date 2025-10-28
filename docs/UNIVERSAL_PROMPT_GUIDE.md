# Universal Prompt Architecture Guide (v1.0.0)

## Overview

The **Universal Prompt** is a single-file system prompt that contains all 8 ScholarshipAI app overlays in one place. Agent3 (AI agents) can load this universal prompt and select only the relevant overlay for the running app.

---

## Architecture

### **Load Order**
```
1. shared_directives.prompt (Global foundation)
2. universal.prompt (All 8 app overlays)
3. Runtime: Select [APP: {app_key}] overlay
```

### **File Structure**
```
docs/system-prompts/
├── shared_directives.prompt   # Global rules, SLOs, KPIs (required)
├── universal.prompt            # All 8 app overlays (v1.0.0)
└── [Individual files for backward compatibility]
    ├── scholarship_api.prompt
    ├── student_pilot.prompt
    ├── provider_register.prompt
    ├── scholar_auth.prompt
    ├── auto_page_maker.prompt
    ├── scholarship_agent.prompt
    ├── scholarship_sage.prompt
    └── executive_command_center.prompt
```

---

## How It Works

### **1. Boot-Time Loading**

When an app starts, it loads prompts in this order:

```python
# Load shared directives (always first)
shared = load_prompt("docs/system-prompts/shared_directives.prompt")

# Load universal prompt (contains all 8 overlays)
universal = load_prompt("docs/system-prompts/universal.prompt")

# Merge for runtime use
system_prompt = f"{shared}\n\n---\n\n{universal}"
```

### **2. Runtime Overlay Selection**

Agent3 receives an `app_key` in the request context:

```python
app_key = "scholarship_api"  # From env, request header, or config
```

Agent3 then:
1. Scans the universal prompt for `[APP: {app_key}]` section
2. Applies **only** that overlay + `[SHARED EXECUTION RULES]`
3. Ignores all other `[APP: ...]` overlays
4. Refuses out-of-scope actions and routes user to correct app

---

## App Keys & Overlays

| App Key | Overlay Section | Purpose |
|---------|----------------|---------|
| `scholar_auth` | `[APP: scholar_auth]` | Identity/consent, PII redaction |
| `student_pilot` | `[APP: student_pilot]` | B2C journey, credit consumption |
| `provider_register` | `[APP: provider_register]` | B2B onboarding, listing fees |
| `scholarship_api` | `[APP: scholarship_api]` | Retrieval/matching, search, funnel |
| `executive_command_center` | `[APP: executive_command_center]` | KPI tracking, daily briefs |
| `auto_page_maker` | `[APP: auto_page_maker]` | SEO pages, attribution |
| `scholarship_agent` | `[APP: scholarship_agent]` | Growth automation, A/B tests |
| `scholarship_sage` | `[APP: scholarship_sage]` | AI advisor, transparency |

---

## Verification Endpoints

### **1. Verify Prompt Loading**
```bash
curl http://localhost:5000/api/prompts/verify
```

**Response:**
```json
{
  "app": "scholarship_api",
  "prompts_loaded": 2,
  "prompts_expected": 2,
  "shared_directives_loaded": true,
  "app_specific_loaded": true,
  "total_size_bytes": 13825,
  "verification_hash": "fd9a8f19cdc8146d",
  "architecture": "universal",
  "prompts": [
    {"name": "shared_directives.prompt", "hash": "736bb45c6f6634ee"},
    {"name": "universal.prompt", "hash": "d1bc5fc7def0d48c"}
  ]
}
```

### **2. List All Prompts**
```bash
curl http://localhost:5000/api/prompts/list
```

### **3. Extract App Overlay**
```bash
curl http://localhost:5000/api/prompts/overlay/scholarship_api
```

**Response:**
```json
{
  "app": "scholarship_api",
  "architecture": "universal",
  "overlay_size_bytes": 836,
  "hash": "d9ec373f40d7bd68",
  "content": "[APP: scholarship_api] overlay content..."
}
```

### **4. Get Merged Prompt**
```bash
curl http://localhost:5000/api/prompts/merge/scholarship_api
```

---

## Benefits of Universal Architecture

### **Single Source of Truth**
- All 8 app overlays in one file
- No drift between individual files
- Easier to maintain consistency

### **Agent3 Runtime Selection**
- One agent can support all 8 apps
- Context-aware overlay selection
- Automatic scope enforcement

### **Version Control**
- Single version number (v1.0.0)
- Single verification hash
- Easier rollback and deployment

### **Backward Compatible**
- Individual files still supported
- Auto-detects architecture (`universal` vs `individual`)
- No breaking changes for existing apps

---

## Must-Emit Events by App

### Scholarship API
- `match_generated(userId, count, avg_score)`
- `scholarship_viewed(scholarshipId)`
- `scholarship_saved(scholarshipId)`
- `application_started(scholarshipId)`
- `application_submitted(applicationId, scholarshipId, revenue_usd)`

### Student Pilot
- `onboarding_started(userId)`
- `credits_purchased(userId, credits, revenue_usd)`
- `application_started(userId, scholarshipId)`
- `application_submitted(userId, scholarshipId, revenue_usd)`

### Provider Register
- `scholarship_posted(scholarshipId, providerId, award_amount, fee_usd)`
- `provider_onboarded(providerId, plan)`
- `listing_updated(scholarshipId, field)`

### Scholar Auth
- `auth_started(actor=User)`
- `auth_verified(userId, ageBand, consentType)`
- `pii_redacted(field, ruleId)`

### Auto Page Maker
- `page_published(slug, topic, geo, template, wordCount)`
- `page_indexed(slug, engine, rank, indexedAt)`
- `page_viewed(slug, sessionId, referrer, utm)`
- `lead_captured(leadId, sourceSlug, sessionId, leadType)`

### Scholarship Agent
- `campaign_launched(campaignId, audience, budget)`
- `campaign_step_completed(campaignId, step)`
- `ab_test_started(testId, variantKeys)`
- `ab_test_converted(testId, variant, conversionEvent)`
- `link_clicked(campaignId, url, utm, sessionId)`

### Scholarship Sage
- `recommendation_shown(userId, scholarshipId, rationaleTag)`
- `recommendation_accepted(userId, scholarshipId)`
- `checklist_created(userId, scholarshipId, checklistId, itemCount)`
- `checklist_completed(userId, checklistType)`

### Executive Command Center
- `kpi_generated(window, mrr, arr, cac, arpu)`
- `daily_brief_posted(timestamp, channel)`
- `scheduler_job_run(jobName, status, duration_ms)`

---

## Global Guardrails (All Apps)

### Responsible AI
- Transparency, bias mitigation
- No ghostwriting or academic dishonesty

### Regulatory
- FERPA/COPPA aligned
- PII redaction by default
- Minimal data storage

### Safety Filters
- Input validation
- Rate limiting
- WAF protection
- Abuse detection

### Red Lines
- Never store SSN or exact home address
- Use IDs (leadId, userId) instead of PII
- For leads: nanoid, not email

---

## Revenue Attribution

### B2C (Student Pilot)
- **Cash-in:** `credits_purchased(revenue_usd)`
- **Consumption:** `application_submitted(revenue_usd)` from credit spending
- **KPI deduplication:** Executive Command Center treats purchase as Revenue, consumption as Usage

### B2B (Provider Register)
- **Fee calculation:** `fee_usd = award_amount * 0.03` (server-side only)
- **Event:** `scholarship_posted(fee_usd, orgId, scholarshipId)`
- **3% platform fee** on all listings

---

## Exception Handling

### Out-of-Scope Actions
```python
# User asks scholarship_api to handle provider signup
# Agent3 response:
{
  "error": "out_of_scope",
  "message": "Provider signup is handled by provider_register app",
  "event": "exception_escalated(scholarship_api, out_of_scope, provider_signup_requested)"
}
```

### Missing Overlay
```python
# app_key not found in universal.prompt
# Agent3 response:
{
  "error": "overlay_missing",
  "message": "Operating under [SHARED] rules only",
  "event": "exception_escalated(unknown_app, overlay_missing, app_key)"
}
```

---

## Operational Next Actions

### 1. Database Migration (All Apps)
```bash
npm run db:push
# Select: + business_events › create table
```

### 2. Verify Events (T+24h)
```sql
SELECT event_name, COUNT(*) 
FROM business_events 
GROUP BY event_name;
```

### 3. Manual KPI Generation (T+48h)
```bash
curl -X POST http://localhost:5000/api/executive/kpi/generate
```

### 4. Automated Daily Brief (T+72h)
- Verify 09:00 UTC brief includes real revenue
- Check Slack webhook delivery

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | Oct 27, 2025 | Initial universal prompt with 8 app overlays |

---

## Support

For questions or issues:
1. Check verification endpoints: `GET /api/prompts/verify`
2. Review event emission logs for errors
3. Escalate via `exception_escalated` event
4. Contact #engineering-kpis Slack channel
