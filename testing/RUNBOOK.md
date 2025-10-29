# E2E Read-Only Testing Runbook

## Overview

This test suite performs read-only production readiness checks on all 8 Scholar AI Advisor apps without making any changes to data or state.

## Quick Start

### 1. Initial Probe (Fastest)

```bash
cd testing/reporting
python3 generate_readiness_report.py
```

This generates a preliminary readiness report in ~30 seconds.

### 2. Backend Tests (API Endpoints)

```bash
cd testing/backend
pip install -r requirements.txt
pytest -v
```

### 3. Frontend Tests (UI Smoke Tests)

```bash
cd testing/frontend
npm install
npx playwright install
npm test
```

## What Gets Tested

### All Apps
- ✅ Availability (HTTP 200-399)
- ✅ TTFB and response times
- ✅ Security headers (HSTS, CSP, X-Frame-Options, etc.)
- ✅ SSL/TLS validity
- ✅ Console errors (frontend apps)

### API Apps (Scholarship API, Scholar Auth)
- ✅ /health endpoint
- ✅ /status endpoint
- ✅ /metrics endpoint
- ✅ /docs or /swagger
- ✅ /openapi.json
- ✅ CORS headers
- ✅ JSON response formats

### Frontend Apps (Public)
- ✅ Landing page loads < 3s
- ✅ SEO: title, meta description, robots.txt, sitemap.xml
- ✅ No blocking console errors
- ✅ Basic accessibility (landmarks, alt text)
- ✅ Key navigation links work (GET only)

### Frontend Apps (Authenticated)
- ✅ Login UI visible
- ✅ Protected routes redirect to login
- ✅ Privacy/terms links present

### Internal Dashboard
- ✅ Dashboard loads
- ✅ Read-only sections render
- ✅ Charts/visualizations load without errors

## Safety Guarantees

### What Tests DO:
- ✅ GET requests only
- ✅ HEAD and OPTIONS requests
- ✅ Capture screenshots and logs
- ✅ Check headers and metadata

### What Tests DO NOT:
- ❌ POST, PUT, PATCH, DELETE requests
- ❌ Submit any forms
- ❌ Create, modify, or delete data
- ❌ Authenticate (unless test credentials provided)
- ❌ Store PII

## Readiness Scoring

- **5/5** - Production-ready (solid availability, performance, security)
- **4/5** - Near-ready (minor issues only)
- **3/5** - Usable with non-critical issues
- **2/5** - Critical issues (broken functionality, severe errors)
- **1/5** - Major blockers (SSL errors, broken root route)
- **0/5** - Not reachable

## Apps Under Test

1. **Auto Com Center** - https://auto-com-center-jamarrlmayes.replit.app
2. **Scholarship Agent** - https://scholarship-agent-jamarrlmayes.replit.app
3. **Scholarship Sage** - https://scholarship-sage-jamarrlmayes.replit.app
4. **Scholarship API** - https://scholarship-api-jamarrlmayes.replit.app
5. **Student Pilot** - https://student-pilot-jamarrlmayes.replit.app
6. **Provider Register** - https://provider-register-jamarrlmayes.replit.app
7. **Auto Page Maker** - https://auto-page-maker-jamarrlmayes.replit.app
8. **Scholar Auth** - https://scholar-auth-jamarrlmayes.replit.app

## Output

All tests generate reports in:
- `testing/reporting/readiness_report_<timestamp>.md`

## Troubleshooting

### Connection Timeouts
- Check app URLs in `shared/config.json`
- Verify apps are deployed and running
- Check network connectivity

### Missing Dependencies
```bash
# Backend
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install && npx playwright install
```

### Test Failures
- Tests are read-only; failures indicate app issues, not test issues
- Check individual app logs for root cause
- Review generated report for specific findings

## Timeline Alignment

This testing framework supports the **72-hour CEO directive** timeline:

- **T+24h:** Test scholarship_api, scholarship_agent
- **T+48h:** Test student_pilot (B2C), provider_register (B2B)
- **T+72h:** Test all remaining apps

Run the probe before each rollout phase to validate readiness.
