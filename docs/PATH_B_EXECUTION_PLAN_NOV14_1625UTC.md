# Path B Execution Plan - CEO Order Nov 14, 16:25 UTC

**Authority**: CEO Executive Order  
**Mode**: Path B (Mirror workspaces under CEO org)  
**Timeline**: 8 hours (16:30-00:30 UTC)  
**Budget**: $5,000 authorized (k6, ESP/SMS, Reserved VMs)

---

## IMMEDIATE: Workspace Mirroring (Platform Team)

**Required Action**: Platform team must mirror 5 workspaces under CEO org

| Workspace | Purpose | Owner | Priority |
|-----------|---------|-------|----------|
| scholar_auth | Identity & auth | Security Lead | P0 |
| scholarship_api | Core API | Platform Lead | P0 |
| auto_com_center | Messaging | Platform Lead | P0 |
| student_pilot | B2C frontend | Frontend Lead | P1 |
| provider_register | B2B frontend | Frontend Lead | P1 |

**Post-Mirror Actions**:
1. Freeze legacy workspaces (read-only)
2. Configure Replit Secrets in mirrored workspaces
3. Prepare DNS cutover plan
4. Grant Agent3 + DRIs access to mirrored workspaces

---

## 8-Hour Execution Timeline

### Hour 0-2 (16:30-18:30 UTC): scholar_auth Gate 0

**Owner**: Security Lead + Agent3  
**Workspace**: scholar_auth (mirrored)

#### Tasks:
1. **RS256 + JWKS**
   - [ ] Generate RSA keypair (4096-bit)
   - [ ] Store private key in Replit Secrets: `JWKS_PRIVATE_KEY`
   - [ ] Publish JWKS endpoint: `/.well-known/jwks.json`
   - [ ] Configure 300s access token TTL
   - [ ] Implement refresh token rotation
   - [ ] Add revocation list support

2. **RBAC Claims**
   - [ ] Define roles: `student`, `provider`, `admin`
   - [ ] Scopes:
     - `student`: `read:scholarships`, `write:applications`, `read:profile`
     - `provider`: `write:scholarships`, `read:applications`, `write:communications`
     - `admin`: `write:*`, `read:*`, `admin:*`
   - [ ] Add claims to JWT payload

3. **OAuth2 Client Credentials (S2S)**
   - [ ] Generate client credentials for 8 services:
     1. scholarship_api
     2. auto_com_center
     3. scholarship_sage
     4. scholarship_agent
     5. auto_page_maker
     6. student_pilot
     7. provider_register
     8. internal_admin
   - [ ] Store in Replit Secrets
   - [ ] Test token issuance

4. **MFA Enforcement**
   - [ ] Email OTP for `admin` + `provider_admin` roles
   - [ ] Enforce at login
   - [ ] Enforce at sensitive actions (password change, email change)

5. **CORS Lockdown**
   ```python
   ALLOWED_ORIGINS = [
     "https://student-pilot.scholarshipai.com",
     "https://provider-register.scholarshipai.com"
   ]
   # NO wildcards, NO localhost in prod
   ```

6. **Health & Audit**
   - [ ] `/health` endpoint
   - [ ] `/readyz` endpoint (DB, config checks)
   - [ ] Audit logging (auth events)
   - [ ] Key rotation SOP documented

#### Evidence Deliverables:
- [ ] JWKS endpoint URL + response
- [ ] Sample JWTs (8 services, redacted)
- [ ] RBAC role matrix
- [ ] MFA flow video/screenshots
- [ ] CORS test logs (allowed/blocked)
- [ ] Key rotation SOP document

---

### Hour 0-2 PARALLEL: GA4 Instrumentation

**Owner**: Agent3 (frontends)  
**Workspaces**: student_pilot, provider_register (mirrored)

#### student_pilot:
```javascript
// First Document Upload event
gtag('event', 'first_document_upload', {
  'event_category': 'activation',
  'event_label': 'student_value_creation',
  'user_id': userId,
  'timestamp': new Date().toISOString()
});

// SPA pageview tracking
gtag('config', 'GA4_MEASUREMENT_ID', {
  'page_path': window.location.pathname
});
```

#### provider_register:
```javascript
// First Scholarship Created event
gtag('event': 'first_scholarship_created', {
  'event_category': 'activation',
  'event_label': 'provider_value_creation',
  'user_id': providerId,
  'timestamp': new Date().toISOString()
});

// Provider verification funnel
gtag('event', 'provider_verification_started', {
  'event_category': 'verification',
  'funnel_step': 1
});
```

#### Evidence Deliverables:
- [ ] GA4 DebugView screenshots (events firing)
- [ ] Dashboard showing activation rates
- [ ] User ID reporting verified

---

### Hour 2-4 (18:30-20:30 UTC): scholarship_api Gate 0

**Owner**: Platform Lead + Agent3  
**Workspace**: scholarship_api (mirrored)

#### Tasks:
1. **JWT Middleware**
   - [ ] Signature validation (RS256 via JWKS)
   - [ ] Claims validation (exp, iat, scope)
   - [ ] Role-based route authorization
   - [ ] Add to all protected endpoints

2. **Circuit Breakers** (NEW)
   ```python
   class CircuitBreaker:
       states: CLOSED, OPEN, HALF_OPEN
       failure_threshold: 5
       timeout: 60s
   ```
   - [ ] Apply to JWKS fetches
   - [ ] Apply to database queries
   - [ ] Apply to external API calls

3. **Request Timeouts** (NEW)
   - [ ] Global request timeout: 5s
   - [ ] Middleware: TimeoutMiddleware
   - [ ] Return 504 on timeout

4. **Connection Pooling**
   - [ ] Verify SQLAlchemy pool: 20-50 connections
   - [ ] Enable PgBouncer (optional)
   - [ ] Test under load

5. **Redis Provisioning**
   - [ ] Provision Redis (Replit addon or Upstash)
   - [ ] Set `RATE_LIMIT_REDIS_URL` in Replit Secrets
   - [ ] Verify /readyz shows redis: "healthy"
   - [ ] Migrate rate limiting to Redis

6. **Reserved VM/Autoscale**
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

7. **OpenAPI Spec**
   - [ ] Publish Swagger UI at /docs
   - [ ] Require JWT auth for /docs access
   - [ ] Document all endpoints

8. **Data Integrity**
   - [ ] Add constraints on scholarship objects
   - [ ] Add constraints on application objects
   - [ ] Validation middleware

9. **Integrations**
   - [ ] Outbound webhook to auto_com_center (notifications)
   - [ ] Data feed endpoint for auto_page_maker

#### Evidence Deliverables:
- [ ] Infrastructure config (autoscale YAML)
- [ ] Connection pool settings
- [ ] Redis provisioning confirmation
- [ ] k6 run ID (250 RPS, P95 ≤120ms, error <0.1%)
- [ ] /readyz snapshot (all healthy)
- [ ] OpenAPI spec URL
- [ ] Circuit breaker implementation
- [ ] Request timeout middleware

---

### Hour 4-6 (20:30-22:30 UTC): auto_com_center Gate 1

**Owner**: Platform Lead + Agent3  
**Workspace**: auto_com_center (mirrored)

#### Tasks:
1. **CORS Lockdown**
   ```python
   ALLOWED_ORIGINS = [
     "https://student-pilot.scholarshipai.com",
     "https://provider-register.scholarshipai.com",
     "https://scholarship-api.scholarshipai.com"  # S2S only
   ]
   ```

2. **S2S Auth**
   - [ ] OAuth2 client_credentials enforcement
   - [ ] Validate tokens from scholar_auth JWKS
   - [ ] Block unauthenticated requests

3. **SendGrid Integration**
   - [ ] Use Replit connector: `connector:ccfg_sendgrid_01K69QKAPBPJ4SWD8GQHGY03D5`
   - [ ] Sandbox mode initially
   - [ ] Domain verification (SPF, DKIM, DMARC)
   - [ ] Bounce webhook: `/webhooks/sendgrid/bounce`
   - [ ] Complaint webhook: `/webhooks/sendgrid/complaint`
   - [ ] Delivery event logging

4. **Twilio Integration**
   - [ ] Use Replit connector: `connector:ccfg_twilio_01K69QJTED9YTJFE2SJ7E4SY08`
   - [ ] Test credentials initially
   - [ ] Dedicated number provisioned
   - [ ] Delivery status webhooks

5. **Email/SMS Templates**
   - [ ] Env-driven template registry
   - [ ] Zero hardcoded URLs
   - [ ] Dynamic link generation (student_pilot, provider_register)

6. **Performance**
   - [ ] k6 canary: 250 RPS, 30 min
   - [ ] P95 ≤120ms
   - [ ] Error rate <0.1%

#### Evidence Deliverables:
- [ ] Domain verification screenshots (SPF, DKIM, DMARC)
- [ ] SendGrid dashboard access
- [ ] Twilio dashboard access
- [ ] Bounce/complaint webhook logs
- [ ] CORS preflight test logs
- [ ] k6 run ID (canary passed)
- [ ] Webhook event flow recording

---

### Hour 6-8 (22:30-00:30 UTC): Validation & Evidence

**Owner**: Agent3 (Program Integrator)

#### Tasks:
1. **scholarship_api Retest**
   - [ ] Run k6 load test (250 RPS, 10 min)
   - [ ] Verify P95 ≤120ms, error <0.1%
   - [ ] Generate before/after charts

2. **auto_page_maker Prep**
   - [ ] Stand up minimal internal endpoint
   - [ ] Queue 20 long-tail SEO pages
   - [ ] Keep behind S2S auth
   - [ ] Review for accuracy + compliance

3. **Evidence Consolidation**
   - [ ] scholar_auth evidence bundle
   - [ ] scholarship_api evidence bundle
   - [ ] auto_com_center evidence bundle
   - [ ] GA4 activation evidence
   - [ ] Upload to `docs/evidence/`

4. **DNS Cutover Plan**
   - [ ] Document DNS changes
   - [ ] Test cutover procedure
   - [ ] Rollback plan
   - [ ] TTL verification

5. **Final Report**
   - [ ] Gate 0 pass/fail per service
   - [ ] Gate 1 pass/fail per service
   - [ ] Go/no-go recommendation for ARR ignition
   - [ ] Risk log with mitigations

---

## Gate 0 Acceptance Criteria (Must-Pass)

### scholar_auth
- ✅ JWKS live at `/.well-known/jwks.json`
- ✅ RBAC claims validated in JWTs
- ✅ MFA enforced (admin/provider_admin)
- ✅ Strict CORS (no wildcards)
- ✅ Audit logs enabled
- ✅ Evidence pack approved

### scholarship_api
- ✅ JWT middleware enforced on all routes
- ✅ OpenAPI published at /docs (auth required)
- ✅ Data constraints active
- ✅ /readyz green under load
- ✅ Canary passes: 250 RPS, P95 ≤120ms, error <0.1%
- ✅ Evidence pack approved

---

## Gate 1 Acceptance Criteria (Messaging Ready)

### auto_com_center
- ✅ Domain verified (SPF/DKIM/DMARC)
- ✅ SendGrid + Twilio integrated
- ✅ Bounce/complaint webhooks live
- ✅ S2S auth enforced
- ✅ Canary passed: 250 RPS, P95 ≤120ms, error <0.1%
- ✅ Evidence pack approved

### Frontends (student_pilot, provider_register)
- ✅ GA4 "First Document Upload" firing (student_pilot)
- ✅ GA4 "First Scholarship Created" firing (provider_register)
- ✅ Events verified in DebugView
- ✅ Dashboard populated

---

## SLOs (Non-Negotiable)

- **Uptime**: 99.9%
- **Latency**: P95 ≤120ms at 250 RPS
- **Error Rate**: <0.1%
- **Canaries**: Must pass before exposing public flows

---

## Risk Controls & Compliance

### FERPA/COPPA
- [ ] Data minimization on logs
- [ ] No PII in analytics payloads
- [ ] Opt-in consent for communications
- [ ] Secure token storage (HttpOnly, Secure, SameSite)
- [ ] Role-scoped access only

### Responsible AI
- [ ] scholarship_sage dark until offline eval complete
- [ ] No bias regressions verified
- [ ] Acceptable precision/recall
- [ ] Model card published before enabling

### Provider Verification
- [ ] GoodHire/Sterling integration (post-Gate 0)
- [ ] No payout until verified
- [ ] No scholar contact until verified

---

## Budget ($5,000 Authorized)

### Infrastructure:
- [ ] Reserved VM (scholar_auth): ~$50/month
- [ ] Reserved VM (scholarship_api): ~$50/month
- [ ] Reserved VM (auto_com_center): ~$50/month
- [ ] Redis (3 instances): ~$30/month

### Testing:
- [ ] k6 Cloud credits: $500

### Messaging:
- [ ] SendGrid Pro plan: ~$90/month
- [ ] Twilio dedicated number: ~$1/month + usage
- [ ] Domain verification: $0

### Fallback:
- [ ] Postmark (if SendGrid DNS >24h): ~$15/month

**Total Estimated**: ~$800/month recurring + $500 one-time

---

## KPIs (Daily Tracking)

### Security
- **Target**: 100% routes behind JWT + RBAC by Hour 4
- **Current**: TBD

### Performance
- **Target**: P95 ≤120ms, error <0.1% at 250 RPS by Hour 8
- **Current**: scholarship_api FAILED (92.1% error, infrastructure)

### Analytics
- **Target**: GA4 activation events firing and visible in DebugView within Hour 2
- **Current**: Not yet implemented

---

## Reporting Cadence

### Hourly Updates (During 8-Hour Sprint)
**Format**: RED/AMBER/GREEN per service  
**Include**:
- Progress on current hour tasks
- k6 run IDs
- /readyz snapshots
- Config diffs
- Evidence artifacts
- Blockers (raise within 15 min)

**Next Update**: Nov 14, 17:30 UTC (Hour 1 checkpoint)

### Final Summary (Hour 8)
- Pass/fail per Gate 0 requirement
- Pass/fail per Gate 1 requirement
- Go/no-go recommendation for ARR ignition
- DNS cutover readiness

---

## Go-Live Alignment

**ARR Ignition Target**: December 1, 2025

**If Gate 0 + Gate 1 Pass by Nov 20**:
- Open controlled beta funnel
- Students + verified providers only
- Messaging live
- Frontends instrumented
- SEO prep in motion (20 pages seeded)

**auto_page_maker** (Hour 6-8):
- Stand up minimal internal endpoint
- Generate 20 long-tail SEO pages
- Keep behind S2S auth
- Publish once security + compliance reviewed

---

## Next Actions (IMMEDIATE)

### Platform Team (NOW):
1. Mirror 5 workspaces under CEO org
2. Freeze legacy workspaces (read-only)
3. Grant Agent3 + DRIs access to mirrored workspaces
4. Configure Replit Secrets in mirrored workspaces

### Agent3 (NOW):
1. ✅ Document Path B execution plan
2. ✅ Begin Hour 2-4 work on scholarship_api (circuit breakers, timeouts)
3. ⏸️ Prepare GA4 instrumentation (pending frontend access)
4. ✅ First hourly update (16:30 UTC)

---

**Prepared By**: Agent3 (Program Integrator)  
**Authority**: CEO Executive Order  
**Date**: Nov 14, 2025, 16:25 UTC  
**Status**: ACTIVE - Awaiting platform team mirroring
