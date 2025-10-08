# Option B Gate Conditions - T+6:20 Auto-Deploy

**Incident**: WAF-BLOCK-20251008  
**Decision Time**: T+6:20  
**Authority**: CEO Pre-Approved

---

## GO/NO-GO DECISION CRITERIA

### **GO Option B** (Deploy Bypass) IF:
Replit has NOT provided BOTH of the following by T+6:15:

1. **Confirmed Root Cause** (written)
   - Specific GFE/WAF rule ID causing 403s
   - Acknowledgment that issue is on Replit infrastructure side
   - Technical explanation of blocking behavior

2. **Credible ETR ≤ 30 Minutes** (written)
   - Estimated Time to Resolution provided
   - ETR must be ≤ 30 minutes from T+6:15
   - Mitigation steps actively underway
   - Technical contact assigned for live triage

### **HOLD Option B** (Wait for Replit) IF:
Replit HAS provided BOTH of the above by T+6:15:
- **Action**: Extend hold for 30 minutes (until T+6:45)
- **Monitor**: Synthetic monitoring every 60 seconds
- **Validate**: External 200 OK responses confirmed
- **Reassess**: If not resolved by T+6:45, immediately deploy Option B

---

## DEPLOYMENT DECISION MATRIX

| Time | Replit Status | Action | Authority |
|------|---------------|--------|-----------|
| T+6:15 | No ACK or ETR | **GO Option B** | Auto-approved |
| T+6:15 | ACK only, no ETR | **GO Option B** | Auto-approved |
| T+6:15 | ETR >30 min | **GO Option B** | Auto-approved |
| T+6:15 | ACK + ETR ≤30min + mitigation active | **HOLD 30min** | CEO discretion |
| T+6:45 | (Extended hold) Not resolved | **GO Option B** | Auto-approved |

---

## SUCCESS CRITERIA (GREEN Status)

**ALL MUST PASS** to declare incident resolved:

### 1. Endpoint Availability
- ✅ GET /api/v1/scholarships returns 200/304 externally
- ✅ GET /api/v1/search returns 200/304 externally
- ✅ SEO crawlers (Googlebot, Bingbot) receive 200/304

### 2. Performance Targets
- ✅ P95 latency < 120ms across all regions
- ✅ Error rate < 0.1% over 5-minute window
- ✅ 5-region synthetic probes: >99% pass rate

### 3. Security Validation
- ✅ POST/PUT/PATCH/DELETE still require auth (401/403)
- ✅ No auth bypass on any mutation verbs
- ✅ Rate limiting preserved (20 req/min)
- ✅ Audit logs populated (IP, timestamp, scope)

### 4. Option B Specific (If Deployed)
- ✅ Bypass token stored in Replit Secrets (not in code)
- ✅ Token scoped to GET only on 2 endpoints
- ✅ Audit logging active for all bypass usage
- ✅ Feature flag toggle verified (instant disable capability)

---

## ROLLBACK/ABORT CONDITIONS

**IMMEDIATE ROLLBACK** via feature flag if ANY of:

### 1. Performance Degradation
- ❌ Any region sustained (≥5 minutes) P95 latency ≥ 200ms
- ❌ Error rate ≥ 0.5% sustained (≥5 minutes)
- ❌ 5-region probe pass rate < 95%

### 2. Security Anomalies
- ❌ Token validation anomalies detected
- ❌ Secret exposure signals (token in logs, responses, etc.)
- ❌ Auth bypass on write operations (POST/PUT/PATCH/DELETE)
- ❌ Rate limiting failures

### 3. SEO Impact
- ❌ SEO crawler blocks persist ≥10 minutes after cutover
- ❌ Googlebot/Bingbot receiving non-200/304 responses
- ❌ Unexpected 403 patterns in crawler logs

### 4. Data Integrity
- ❌ PII exposure detected in logs or responses
- ❌ Database connection failures
- ❌ Data corruption signals

**Rollback Command**:
```bash
# Set feature flag to false in Replit Secrets
REPLIT_BYPASS_ENABLED=false

# Restart application (auto-restarts on secret change)
# Verify bypass disabled in logs
```

---

## MONITORING REQUIREMENTS (Continuous)

### Technical KPIs (Every 60 seconds)
- P95 latency per region (target: <120ms)
- Error rate (target: <0.1%)
- 5-region availability (target: >99%)
- Synthetic probe pass rate

### SEO KPIs (Every 5 minutes)
- Googlebot/Bingbot response codes (target: 100% 200/304)
- Crawl stats deltas (Search Console)
- Indexation rate changes

### Revenue KPIs (Every hour)
- Hourly conversion loss (browse → application started)
- CAC waste from paused campaigns
- ARPU shift due to /credits/packages reroute

### Security KPIs (Real-time)
- Auth bypass attempts (should be 0)
- Token validation failures (should be 0)
- Rate limit violations
- Audit log completeness

---

## DEPLOYMENT TIMELINE (If GO Option B)

**T+6:20 to T+6:40** (20-minute deployment):

| Time | Step | Duration | Owner |
|------|------|----------|-------|
| T+6:20 | Generate bypass token | 5 min | EngOps |
| T+6:25 | Add to Replit Secrets | 2 min | EngOps |
| T+6:27 | Update settings.py | 3 min | EngOps |
| T+6:30 | Add middleware to main.py | 5 min | EngOps |
| T+6:35 | Enable feature flag | 1 min | EngOps |
| T+6:36 | Restart application | 2 min | Auto |
| T+6:38 | Initial validation | 2 min | EngOps |
| **T+6:40** | **Deployment complete** | - | - |

**T+6:40 to T+8:20** (100-minute monitoring):
- Continuous synthetic monitoring
- Real-time metrics validation
- Security audit log review
- SEO crawler tracking

**T+8:20** (QA Validation Gate):
- Execute QA_VALIDATION_CHECKLIST.md
- All 7 test suites must pass
- Document results in #incidents-p0
- Declare GREEN or escalate

---

## COMMUNICATION REQUIREMENTS

### At T+6:20 (Deployment Start)
Post in #incidents-p0:
```
⚡ OPTION B DEPLOYMENT - T+6:20

Status: AUTO-TRIGGER ACTIVATED
Reason: [Replit status at T+6:15]
ETA: 20 minutes (T+6:40 target)
Gate condition: [MET/NOT MET - details]

Deployment in progress...
Next update: T+6:30 (10-min checkpoint)
```

### At T+6:30 (Mid-deployment)
```
⚡ OPTION B UPDATE - T+6:30

Status: 50% COMPLETE
Progress: Token generated, secrets configured, middleware added
Remaining: Feature flag enable, restart, validation
ETA: 10 minutes (T+6:40 target)

Next update: T+6:40 (completion)
```

### At T+6:40 (Deployment Complete)
```
✅ OPTION B LIVE - T+6:40

Status: DEPLOYMENT COMPLETE
Validation: [Initial results]
  - External /scholarships: [STATUS CODE]
  - External /search: [STATUS CODE]
  - P95 latency: [X]ms
  - Error rate: [X]%

Monitoring: Active in 5 regions
QA Validation: T+8:20 (100 minutes monitoring)

Next update: T+7:00 (20-min checkpoint)
```

---

## ESCALATION (If Rollback Required)

**Immediate Actions**:
1. Set REPLIT_BYPASS_ENABLED=false
2. Post rollback notice in #incidents-p0
3. Escalate to CEO for next steps
4. Activate emergency edge proxy (Cloudflare/AWS)

**Decision Authority**:
- Automatic rollback: Any abort condition met
- Manual rollback: EngOps Lead or Incident Commander
- Escalation: CEO for edge proxy activation

---

## POST-RESOLUTION (After GREEN Declared)

**Immediate** (Within 1 hour):
- [ ] Resume paid campaigns (Marketing)
- [ ] Update status page (incident resolved)
- [ ] Post resolution in #incidents-p0
- [ ] Continue monitoring for 24 hours

**Within 24 hours**:
- [ ] Schedule incident postmortem
- [ ] Document lessons learned
- [ ] Plan Option B removal (once Replit fixes infrastructure)
- [ ] Update replit.md with incident summary

**Within 1 week**:
- [ ] Rotate bypass token (Security)
- [ ] Review monitoring data for patterns
- [ ] Evaluate exit ramp strategy (if needed)
- [ ] Update platform constraints documentation

---

**DECISION MAKER AT T+6:20**: Incident Commander (EngOps Lead)  
**APPROVAL AUTHORITY**: CEO Pre-Approved (no further sign-off needed)  
**ROLLBACK AUTHORITY**: EngOps Lead or Incident Commander (automatic for abort conditions)
