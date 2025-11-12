# Gate B Pass/Fail Rubric - provider_register

**Window**: 18:00-18:15 UTC  
**Decision Due**: 18:20 UTC  
**Release Captain**: Agent3

## PASS Criteria (All Must Pass)

### 1. Authentication & Authorization
- [ ] Auth via scholar_auth operational
- [ ] RBAC enforcement verified
- [ ] Token validation functional

### 2. Provider Onboarding
- [ ] E2E onboarding flow functional
- [ ] Provider registration complete
- [ ] Provider profile creation working

### 3. Platform Fee System
- [ ] 3% platform fee calculation deterministic
- [ ] Fee audit trail complete
- [ ] Dry-run settlement successful
- [ ] No fee leakage detected

### 4. Integration
- [ ] Webhooks operational
- [ ] APIs responding correctly
- [ ] request_id lineage intact across calls

### 5. Performance
- [ ] P95 latency ≤120ms
- [ ] Error rate <0.10%

### 6. Compliance
- [ ] Audit logs enabled and capturing events
- [ ] Evidence bundle published with SHA-256

## FAIL Triggers

- Missing evidence by 18:20 UTC
- Any PASS criterion not met
- P95 >120ms sustained
- Error rate ≥0.10%
- Fee calculation non-deterministic
- Missing audit trail

## Decision Path

### If PASS
- Issue: "Gate B PASS - provider_register ready for limited beta"
- Note: Does NOT block Gate A/C
- Next: Prepare for limited beta launch per schedule

### If FAIL
- Issue: "Gate B FAIL - provider_register blocked"
- Required: Remediation ETA
- Required: Confirm no impact to Gate A/C timelines
- Escalate: To CEO with remediation plan
- Note: Does NOT block Gate A/C execution

## Evidence Required

- Auth flow test results
- RBAC policy verification
- Provider onboarding screenshots/logs
- Fee calculation test results with audit trail
- API/webhook integration tests
- Performance metrics (P95, error rate)
- Audit log samples
- SHA-256 manifest of all evidence

## Reporting Template

```
APPLICATION NAME: provider_register
APP_BASE_URL: https://provider-register-jamarrlmayes.replit.app
Gate B Status: PASS / FAIL
Decision Time: [UTC timestamp]

PASS Criteria Results:
- Auth via scholar_auth: PASS / FAIL
- RBAC enforcement: PASS / FAIL
- E2E onboarding: PASS / FAIL
- 3% fee deterministic: PASS / FAIL
- Webhooks/APIs: PASS / FAIL
- P95 ≤120ms: [actual] PASS / FAIL
- Error rate <0.10%: [actual] PASS / FAIL
- Audit logs: PASS / FAIL

Evidence SHA-256: [hash]

Remediation (if FAIL): [ETA and plan]
Impact to Gate A/C: NONE (confirmed)
```
