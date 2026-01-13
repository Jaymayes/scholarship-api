# GO/NO-GO Cutover Plan

**RUN_ID**: CEOSPRINT-20260114-CUTOVER-V2-038
**Protocol**: AGENT3_HANDSHAKE v30
**Status**: PENDING CEO APPROVAL

---

## Prerequisites (Before Cutover)

| Requirement | Status | Notes |
|-------------|--------|-------|
| All V2 services deployed | ⏳ PENDING | CEO must create workspaces |
| Functional deep-dive PASS | ⏳ PENDING | All endpoints verified |
| P95 ≤ 120ms | ⏳ PENDING | 10-minute test |
| Second-confirmation (2-of-3) | ⏳ PENDING | HTTP+Trace; logs; A8 |
| A8 round-trip verified | ⏳ PENDING | POST+GET checksums |
| Production remains frozen | ✅ YES | FREEZE_LOCK=1 |

---

## Cutover Steps

### Phase 1: Shadow Mode (24h)

1. Deploy V2 services to production URLs (separate workspaces)
2. Enable shadow=true flag on all A8 events
3. Route 5% traffic to V2 (canary)
4. Monitor error rates, latency, conversion parity

### Phase 2: Routing Switch (HITL Required)

1. **CEO approval required**: Log HITL-CEO-XXX in hitl_approvals.log
2. Map A1/A5 flows to OnboardingOrchestrator-v2
3. Redirect /upload to DocumentHub-v2
4. Switch DataService queries to saa-core-data-v2
5. Maintain legacy routes as fallback

### Phase 3: Validation

1. Run INCIDENT VERIFY (032) with Scorched Earth
2. Verify second-confirmation for all services
3. Confirm P95 ≤ 120ms
4. Verify B2B lineage (3% + 4x)
5. Verify B2C readiness (pk_* + stripe.js + CTA)

### Phase 4: Re-Freeze

1. Execute REFREEZE (034)
2. Rebuild drift baselines for V2 services
3. Update version_manifest.json
4. Regenerate golden bundle
5. POST + GET checksum via A8

---

## Backout Plan (< 5 minutes)

1. Revert routing to legacy A1-A8 endpoints
2. No data migration required (DataService-v2 uses separate tables)
3. Legacy services remain operational during cutover window
4. If rollback needed: disable V2 routing, verify legacy health

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Data loss | Separate V2 tables; no migration of existing data |
| Auth regression | A1 remains primary; V2 orchestrator calls A1 |
| Payment failure | Stripe safety paused (4/25); no live charges |
| Latency spike | Circuit breakers prevent cascade |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Error rate | < 1% |
| P95 latency | ≤ 120ms |
| Upload conversion | ≥ baseline |
| A8 ingestion | ≥ 99% |
| Second-confirmation | 2-of-3 all services |

---

## Approval

| Step | Approver | Signature |
|------|----------|-----------|
| Cutover authorization | CEO | _______________ |
| Backout trigger threshold | CEO | Error rate > 5% OR P95 > 200ms |
| Re-freeze confirmation | CEO | _______________ |

---

## Attestation

After CEO HITL and successful switch + re-freeze:

> "Attestation: VERIFIED LIVE (V2 CUTOVER) — Golden Record Updated"
