# Gate 0 Execution Plan - CEO Orders (Nov 14, 2025)

**Authority**: CEO Executive Order  
**Deadline**: Nov 15, 10:30 AM MST  
**Decision Point**: Nov 14, 16:10 UTC (T+30 minutes)  
**Budget Approved**: $1,500 (k6 Cloud) + $2,500 (ESP/SMS) + Reserved VM/Redis

---

## Path Selection (T+30 Decision)

### Path A: Workspace Access Granted (Preferred)
**Trigger**: Ops grants access to scholar_auth, scholarship_api, auto_com_center by 16:10 UTC  
**Execution**: Sequential workspace execution in existing environments  
**Timeline**: 8 hours (Hour 0-8)

### Path B: Direct Control (Fallback)
**Trigger**: No access granted by 16:10 UTC  
**Execution**: Mirror workspaces under CEO org → Execute Gate 0 → DNS cutover  
**Authority**: CEO authorized direct control

---

## Non-Negotiable Gate 0 Go-Live Bars

### 1. scholar_auth (Hour 0-2)

**Owner**: Security Lead with Agent3 support  
**Duration**: 2 hours

#### Requirements:
- [ ] **RS256 JWTs via JWKS**
  - JWKS endpoint published
  - 300s TTL configured
  - Key rotation SOP documented
  
- [ ] **RBAC Claims**
  - `student`: read:scholarships, write:applications, read:profile
  - `provider`: write:scholarships, read:applications, write:communications
  - `admin`: write:*, read:*, admin:*
  
- [ ] **M2M Client Credentials**
  - Generate tokens for 8/8 services:
    1. scholarship_api
    2. auto_com_center
    3. scholarship_sage
    4. scholarship_agent
    5. auto_page_maker
    6. student_pilot
    7. provider_register
    8. [internal admin]
  
- [ ] **MFA Enforcement**
  - Email OTP for admin + provider_admin roles
  - Enforce at login + sensitive actions
  
- [ ] **Strict CORS Allowlist**
  ```python
  ALLOWED_ORIGINS = [
    "https://student-pilot-prod.scholarshipai.com",
    "https://student-pilot-staging.scholarshipai.com",
    "https://provider-register-prod.scholarshipai.com",
    "https://provider-register-staging.scholarshipai.com"
  ]
  # NO wildcards
  ```

- [ ] **Replit Secrets** (NO hardcoded credentials)
  - JWT_SECRET_KEY → Replit Secrets
  - JWKS_PRIVATE_KEY → Replit Secrets
  - MFA_SMTP_PASSWORD → Replit Secrets

#### Evidence Required:
- Sample JWTs for all 8 services (redacted)
- JWKS endpoint URL + response
- RBAC role matrix
- MFA flow proof (video/screenshots)
- CORS test log (allowed/blocked requests)

---

### 2. scholarship_api (Hour 2-4)

**Owner**: Platform Lead with Agent3 support  
**Duration**: 2 hours

#### Requirements:
- [ ] **JWT Validation Middleware**
  - Signature verification (RS256)
  - Claims validation (exp, iat, scope)
  - Role-based route authorization
  
- [ ] **Strict CORS** (mirror scholar_auth allowlist)

- [ ] **Connection Pooling**
  ```python
  DATABASE_POOL_SIZE = 20
  DATABASE_MAX_OVERFLOW = 10
  DATABASE_POOL_RECYCLE = 3600
  ```

- [ ] **Redis Provisioning**
  - Purpose: Rate limiting + JWKS cache
  - Configuration: RATE_LIMIT_REDIS_URL in Replit Secrets
  - Verify: /readyz shows redis: "healthy"

- [ ] **Reserved VM or Autoscale**
  ```yaml
  deployment:
    type: autoscale
    min_instances: 2
    max_instances: 10
    triggers:
      cpu: 70%
      latency_p95: 100ms
      error_rate: 1%
  ```

- [ ] **/readyz Health Checks**
  ```json
  {
    "checks": {
      "database": "healthy",
      "redis": "healthy",
      "auth_jwks": "healthy",
      "configuration": "healthy"
    }
  }
  ```

- [ ] **OpenAPI Documentation**
  - Served at /docs
  - JWT auth documented
  - All endpoints documented

#### Performance Requirements:
- **Load Test**: 250-300 RPS for 10 minutes
- **P95 Latency**: ≤120ms
- **Error Rate**: ≤0.5%
- **Tool**: k6 (Cloud upload approved)

#### Circuit Breakers & Retry (CEO Note):
> "If synchronous hotspots persist, apply retry/backoff and circuit-breakers on client paths to prevent cascading failures"

- [ ] Request timeouts (5s max)
- [ ] Circuit breakers on external calls
- [ ] Exponential backoff on JWKS fetch

#### Evidence Required:
- Infrastructure config (Terraform/YAML)
- Connection pool settings
- Redis provisioning confirmation
- k6 run ID + summary (P95 ≤120ms, error ≤0.5%)
- Before/after latency charts
- /readyz snapshot (all healthy)
- OpenAPI spec URL

---

### 3. auto_com_center (Hour 4-6)

**Owner**: Platform Lead  
**Duration**: 2 hours

#### Requirements:
- [ ] **SendGrid Integration** (Replit Connector)
  - Integration ID: `connector:ccfg_sendgrid_01K69QKAPBPJ4SWD8GQHGY03D5`
  - Domain verification (SPF, DKIM, DMARC)
  - Templates parameterized with env URLs
  - Bounce/complaint webhooks configured

- [ ] **Twilio Integration** (Replit Connector)
  - Integration ID: `connector:ccfg_twilio_01K69QJTED9YTJFE2SJ7E4SY08`
  - SMS sender verified
  - Delivery status webhooks

- [ ] **Service-to-Service Auth**
  - M2M token from scholar_auth
  - Validate tokens on webhook endpoints

- [ ] **Webhook/Trigger Endpoint**
  - Accept signed requests only
  - Rate limiting enabled
  - Error handling with retries

#### Performance Requirements:
- **Canary**: 250 RPS for 30 minutes
- **Error Rate**: ≤0.5%
- **Tool**: k6

#### Evidence Required:
- SendGrid domain verification screenshots
- Twilio sender verification screenshots
- Provider dashboard access proof
- k6 run ID + summary
- Webhook configuration

---

## Hour 6-8: Validation & Evidence Collection

### scholarship_api Retest
- [ ] Run k6 load test (250-300 RPS, 10 min)
- [ ] Validate P95 ≤120ms, error ≤0.5%
- [ ] Generate charts (before/after comparison)
- [ ] Export k6 Cloud run ID

### Evidence Package Assembly
- [ ] scholar_auth evidence bundle
- [ ] scholarship_api evidence bundle
- [ ] auto_com_center evidence bundle
- [ ] Upload to `docs/evidence/`

### Gate 0 Decision Criteria
✅ **PASS** if:
- All 3 services meet go-live bars
- Performance tests pass
- Evidence complete
→ Proceed to Gate 1, ARR Ignition Nov 20

❌ **FAIL** if:
- Critical gaps remain
- Performance tests fail after remediation
→ Pivot to soft launch, defer full scale

---

## Gate 1-2 Requirements (Unblock After Gate 0)

### student_pilot + provider_register (Frontend Lead)
- [ ] Eliminate hardcoded URLs (env-driven only)
- [ ] Auth flow against scholar_auth
- [ ] JWT attached to all API calls
- [ ] Standardized error handling
- [ ] **GA4 Events**: "First Document Upload" (North Star activation metric)

### scholarship_agent
- [ ] M2M auth to scholarship_api
- [ ] Structured logging
- [ ] Alerting for background failures
- [ ] Notification triggers to auto_com_center

---

## Risk, Compliance, Responsible AI

### No Black Box Services (CEO Directive)
> "No 'black box' services for critical decisions. Maintain explainability and audit trails for auth, matching, and automated actions"

- [ ] Audit logging for all auth decisions
- [ ] Decision traces in scholarship_sage recommendations
- [ ] Human-on-the-loop approval gates for high-risk changes

### Bias & Fairness
- [ ] Document data sources for recommendations
- [ ] Add fairness checks to matching logic
- [ ] Monitor for disparate impact at scale

### Secrets & S2S Security
- [ ] **ALL secrets in Replit Secrets** (NO inline keys)
- [ ] Service identity enforcement
- [ ] Authorization consistent across apps

---

## Scope Freeze (CEO Order)

**Effective Immediately**: No net-new features until Gate 0/1 bars pass.

**Allowed Work**:
- ✅ Security hardening
- ✅ Performance optimization
- ✅ Integration work
- ✅ Testing

**Rejected Work**:
- ❌ New features
- ❌ New secrets in code
- ❌ CORS expansion beyond allowlist

---

## Testing Hierarchy (CEO Directive)

Apply in order:
1. **Unit Tests**: Individual functions
2. **Integration Tests**: Service interactions
3. **System/E2E Tests**: Full user journeys

**No Go-Live Until**:
- E2E Student Journey passes (signup → search → apply)
- E2E Provider Journey passes (onboard → create scholarship → review applicants)
- All tests have signed evidence
- Defects triaged

---

## Reporting Cadence

### During Gate 0 Execution (Hour 0-8)
**Frequency**: Hourly  
**Format**: RED/AMBER/GREEN by service  
**Include**:
- k6 run IDs
- /readyz snapshots
- Config diffs
- Rolling risk log

### Post Gate 0 (Until Gate 2)
**Frequency**: Twice daily  
**Format**: Status report + blockers

### Post Gate 2
**Frequency**: Daily  
**Format**: KPI dashboard

---

## KPIs (CEO Tracking)

### Platform Readiness
- Gate 0 pass (Y/N)
- P95 latency at 250-300 RPS
- Error rate on core APIs

### B2C Funnel Instrumentation
- % sign-ups reaching "First Document Upload"
- Conversion to paid credits (ARPU baseline)
- SEO landing flow support (Auto Page Maker)

### B2B Ramp Signals
- # providers with verified accounts
- # providers with ≥1 listed scholarship
- Average time-to-first-listing

---

## Budget Approvals

✅ **k6 Cloud**: Up to $1,500  
✅ **SendGrid/Twilio Onboarding**: Up to $2,500  
✅ **Reserved VM/Redis**: As required for performance SLOs  
✅ **Contingency Platform**: If Replit insufficient, quantified cost/performance comparison required

---

## Agent3 Authorities (CEO Grant)

**You are authorized to**:
1. ✅ Proceed on Path A or Path B based on T+30 outcome
2. ✅ Freeze any work competing with Gate 0/1
3. ✅ Reject changes introducing new secrets in code
4. ✅ Reject CORS expansion beyond allowlist
5. ✅ Mirror workspaces under CEO org (if Path B)
6. ✅ Cut over DNS when evidence meets bars
7. ✅ Freeze legacy workspaces post-cutover
8. ✅ Return with migration proposal if platform insufficient

---

## Decision Timeline

| Time | Event | Action |
|------|-------|--------|
| Nov 14, 16:10 UTC | T+30 Decision Point | Path A or Path B |
| Nov 14, 16:10-18:10 UTC | Hour 0-2 | scholar_auth hardening |
| Nov 14, 18:10-20:10 UTC | Hour 2-4 | scholarship_api security/perf |
| Nov 14, 20:10-22:10 UTC | Hour 4-6 | auto_com_center integrations |
| Nov 14, 22:10-00:10 UTC | Hour 6-8 | Validation + evidence |
| Nov 15, 10:30 AM MST | Gate 0 Decision | PASS/FAIL |

---

## Next Actions (Immediate)

### Now → T+30 (16:10 UTC)
1. Monitor for workspace access grant
2. Prepare Path B mirroring procedure
3. Document Replit integrations (SendGrid, Twilio)
4. Stage k6 Cloud account setup

### At T+30 (16:10 UTC)
**IF** access granted:
→ Execute Path A (Sequential Workspace Execution)

**IF** no access:
→ Execute Path B (Mirror workspaces, DNS cutover)

---

**Prepared By**: Agent3 (Program Integrator)  
**Authority**: CEO Executive Order  
**Date**: Nov 14, 2025, 15:45 UTC  
**Status**: ACTIVE - Awaiting T+30 decision
