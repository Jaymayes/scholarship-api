# Universal E2E Test Framework - Operator Guide

## Quick Start (30 seconds)

### Test All Apps
```bash
cd testing/reporting
python3 generate_readiness_report.py
```

### Test Single App
```bash
# Use the CEO-approved universal prompt with Agent3
# Pass the app URL as input
```

---

## What This Framework Does

✅ **Read-only assessment** - No data modifications  
✅ **Production-ready validation** - Aligned to T+24h, T+48h, T+72h gates  
✅ **Consistent scoring** - 0–5 scale across all 8 apps  
✅ **Evidence collection** - Security, performance, SEO, accessibility  

---

## Framework Structure

```
testing/
├── UNIVERSAL_TEST_PROMPT_CEO_APPROVED.txt   ⭐ Main prompt for Agent3
├── OPERATOR_GUIDE.md                        📖 This file
├── RUNBOOK.md                               📋 Detailed procedures
├── shared/
│   └── config.json                          🔧 All 8 app URLs
├── reporting/
│   ├── generate_readiness_report.py         🚀 Quick probe script
│   ├── report_template.md                   📝 Manual report template
│   └── readiness_report_*.md                📊 Generated reports
├── backend/
│   ├── requirements.txt
│   └── tests/test_readonly_endpoints.py     🧪 API endpoint tests
└── frontend/
    └── tests/smoke.spec.js                  🧪 UI smoke tests
```

---

## The 8 Apps Under Test

| # | App | Type | URL | T+ Gate |
|---|-----|------|-----|---------|
| 1 | Auto Com Center | Admin Dashboard | https://auto-com-center-jamarrlmayes.replit.app | T+72h |
| 2 | Scholarship Agent | Public Web | https://scholarship-agent-jamarrlmayes.replit.app | T+24h |
| 3 | Scholarship Sage | Public Web | https://scholarship-sage-jamarrlmayes.replit.app | T+72h |
| 4 | **Scholarship API** | **API Backend** | https://scholarship-api-jamarrlmayes.replit.app | **T+24h** |
| 5 | **Student Pilot** | **Auth Web (B2C)** | https://student-pilot-jamarrlmayes.replit.app | **T+48h** 🔥 |
| 6 | **Provider Register** | **Public Web (B2B)** | https://provider-register-jamarrlmayes.replit.app | **T+48h** 🔥 |
| 7 | Auto Page Maker | Public Web (SEO) | https://auto-page-maker-jamarrlmayes.replit.app | T+72h |
| 8 | Scholar Auth | Auth Service | https://scholar-auth-jamarrlmayes.replit.app | T+72h |

**🔥 Revenue-critical apps** (T+48h): Student Pilot (B2C), Provider Register (B2B)

---

## Readiness Scoring (0–5)

| Score | Status | Meaning |
|-------|--------|---------|
| **5** | ✅ Production-ready | Solid availability, performance, security |
| **4** | 🟢 Near-ready | Minor issues only |
| **3** | 🟡 Usable | Non-critical issues present |
| **2** | 🔴 Critical issues | Broken functionality, severe errors |
| **1** | ❌ Major blockers | SSL errors, JS fails, missing root route |
| **0** | ❌ Not reachable | DNS/connection failed |

---

## Rollout Gate Requirements

### T+24h Infrastructure Gate
- **Scholarship API**: Score ≥4
- **Scholarship Agent**: Score ≥4

### T+48h Revenue Gate (CRITICAL)
- **Student Pilot** (B2C): Score = 5 (must be production-ready)
- **Provider Register** (B2B): Score = 5 (must be production-ready)

### T+72h Full Ecosystem Gate
- **All apps**: Score ≥4
- **Auto Page Maker** (SEO): Score = 5
- **Scholar Auth**: Score = 5

---

## Running Tests

### Option 1: Quick Probe (Recommended First)

**Time:** ~30 seconds  
**Coverage:** All 8 apps, basic checks

```bash
cd testing/reporting
python3 generate_readiness_report.py

# View report
cat readiness_report_*.md
```

**What it checks:**
- DNS/TLS reachability
- HTTP status codes
- TTFB performance
- Security headers (6 types)
- API endpoints (for API apps)

### Option 2: Backend API Tests

**Time:** ~2 minutes  
**Coverage:** Deep API endpoint validation

```bash
cd testing/backend
pip install -r requirements.txt
pytest -v tests/test_readonly_endpoints.py
```

**What it checks:**
- All read-only endpoints
- JSON response validation
- CORS headers
- OpenAPI documentation
- Response timing

### Option 3: Frontend UI Tests

**Time:** ~5 minutes  
**Coverage:** Visual/interactive validation

```bash
cd testing/frontend
npm install
npx playwright install
npm test
```

**What it checks:**
- Page load without errors
- Console error detection
- Screenshot capture
- Form submission blocking (safety)
- Navigation link validation

### Option 4: Agent3 with Universal Prompt

**Time:** Varies by depth  
**Coverage:** App-specific module execution

```bash
# 1. Copy UNIVERSAL_TEST_PROMPT_CEO_APPROVED.txt
# 2. Paste into Agent3 system prompt
# 3. Ask Agent3 to test specific app or "all"
```

**What it checks:**
- All global evidence items
- App-specific module criteria
- Comprehensive findings
- Actionable recommendations

---

## Understanding the Output

### Quick Probe Report Structure

```markdown
## Executive Summary
- Total Apps: 8
- Reachable: X/8
- Average Readiness Score: X.X/5.0

## Readiness Summary (Table)
| App | Type | Status | TTFB | Score | Issues |

## Detailed Findings (Per App)
### [App Name]
- URL
- Reachable: Yes/No
- Status Code
- TTFB
- Security Headers (present/missing)
- API Endpoints (if applicable)
- Issues
- Readiness Score: X/5
```

### Key Metrics to Watch

1. **Reachability** - ✅ or ❌
2. **TTFB** - Target: < 500ms (< 200ms excellent)
3. **Security Headers** - Target: 5–6/6 present
4. **Readiness Score** - Target: ≥4 (5 for revenue apps)

---

## Interpreting Results

### Green Flags ✅

- Score 5/5
- All security headers present
- TTFB < 200ms
- Zero console errors
- SEO basics present (public apps)

### Yellow Flags 🟡

- Score 3–4/5
- 1–2 missing security headers (non-critical)
- TTFB 200–500ms
- Minor console warnings
- SEO partially present

### Red Flags 🔴

- Score 0–2/5
- Missing CSP or HSTS
- TTFB > 1000ms
- Critical console errors
- HTTP 404/500 errors
- SSL/TLS issues

---

## Common Issues and Fixes

### Issue: App Returns 404 on Root
```
Cause: Missing root route handler
Fix: Add route for "/" in app routing configuration
Example: Auto Com Center currently has this issue
```

### Issue: App Not Reachable
```
Cause: App not deployed or not running
Fix: 
  1. Verify deployment status
  2. Check app logs
  3. Restart app service
Example: Scholarship Sage currently has this issue
```

### Issue: Missing Security Headers
```
Cause: Headers not configured in middleware
Fix: Add security headers to response middleware
Priority: CSP, HSTS, X-Frame-Options
```

### Issue: Slow TTFB (> 500ms)
```
Cause: Cold start, slow backend, or network issues
Fix:
  1. Check server logs for slow queries
  2. Optimize cold start (e.g., keep-alive)
  3. Add caching where appropriate
```

---

## Safety Guarantees

### What Tests DO ✅

- GET, HEAD, OPTIONS requests only
- Read existing data
- Capture screenshots and logs
- Check headers and metadata
- Measure performance

### What Tests DO NOT ❌

- POST, PUT, PATCH, DELETE
- Create, modify, or delete data
- Submit forms
- Authenticate with real credentials
- Store PII
- Bypass rate limits

---

## Rate Limits and Safety

The testing framework respects:

- **1 request per unique path per 10 seconds**
- **Max 20 requests per app per run**
- **Exponential backoff on 429/5xx**
- **robots.txt compliance**
- **User-Agent identification**: `ScholarAI-ReadOnlyProbe/1.0`

---

## Timeline Alignment

### Today (T+0)
✅ Testing framework deployed  
✅ Initial readiness assessment complete  

### T+24h (October 30, 2025)
- Test: Scholarship API, Scholarship Agent
- Target: Both ≥4

### T+48h (October 31, 2025) 🔥 CRITICAL
- Test: Student Pilot, Provider Register
- Target: Both = 5 (production-ready for revenue events)

### T+72h (November 1, 2025) 🎯 CEO DEADLINE
- Test: All 8 apps
- Target: All ≥4; Auto Page Maker and Scholar Auth = 5

---

## Troubleshooting

### Python Script Fails
```bash
# Check Python version (need 3.7+)
python3 --version

# Install dependencies
pip install requests

# Run with verbose output
python3 -v generate_readiness_report.py
```

### Network Timeout
```bash
# Increase timeout in script (default: 10s)
# Check your internet connection
# Verify app URLs are correct in shared/config.json
```

### Playwright Issues
```bash
# Install browsers
npx playwright install

# Clear cache and reinstall
rm -rf node_modules
npm install
npx playwright install
```

---

## Best Practices

### Before Each Rollout Phase

1. **Run quick probe** - Get baseline scores
2. **Fix critical issues** - Address score 0–2 apps
3. **Re-run probe** - Verify fixes
4. **Document findings** - Add to report
5. **Proceed to next phase** - Only if gates passed

### During Testing

1. **Start with quick probe** - Fastest feedback
2. **Deep dive on failures** - Use backend/frontend tests
3. **Compare to previous runs** - Track improvements
4. **Focus on gate requirements** - Prioritize T+48h revenue apps

### After Testing

1. **Archive reports** - Keep timestamped reports
2. **Track trends** - Monitor score changes over time
3. **Update runbook** - Document new issues/fixes
4. **Share findings** - Report to team/CEO

---

## Contact and Support

- **Framework Location**: `testing/` directory
- **CEO-Approved Prompt**: `UNIVERSAL_TEST_PROMPT_CEO_APPROVED.txt`
- **Detailed Procedures**: `RUNBOOK.md`
- **Configuration**: `shared/config.json`

---

## Quick Reference Commands

```bash
# Quick probe (all apps)
cd testing/reporting && python3 generate_readiness_report.py

# View latest report
cat testing/reporting/readiness_report_*.md | head -50

# Backend tests
cd testing/backend && pytest -v

# Frontend tests
cd testing/frontend && npm test

# Update app URLs
vim testing/shared/config.json
```

---

**Version:** 1.0 (CEO-Approved)  
**Last Updated:** October 29, 2025  
**Status:** Production-ready  
**Alignment:** 72-hour CEO directive rollout
