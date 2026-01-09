# A8 Telemetry Wiring Verdict - A2
**Generated**: 2026-01-09T09:45:00Z  
**Protocol**: v3.5.1  
**Directive**: AGENT3_HANDSHAKE v27

## Telemetry Schema Compliance

### Required Fields (per CEO JSON)

| Field | Status | Notes |
|-------|--------|-------|
| timestamp | ✅ Enforced | ts_utc in schema |
| app_id | ✅ Enforced | Required field |
| route | ✅ Available | From request path |
| status | ✅ Available | HTTP status code |
| p95_ms | ✅ Available | From metrics |
| trace_id | ✅ Enforced | HTTP 428 if missing |
| idempotency_key | ✅ Enforced | HTTP 428 if missing |
| finance_metrics | ✅ Available | In properties |
| revenue_event_id | ✅ Available | In properties |

### Header Enforcement

| Header | Enforcement | HTTP Code |
|--------|-------------|-----------|
| X-Idempotency-Key | Required | 428 if missing |
| X-Trace-Id | Required | 428 if missing |
| x-scholar-protocol | Required | 400 if invalid |

### Dedup Rules

| Rule | Implementation |
|------|----------------|
| Key composition | idempotency_key + trace_id |
| Dedupe window | 15 minutes |
| ON CONFLICT | DO NOTHING (PostgreSQL) |

### Sampling Rules

| Event Type | Sample Rate |
|------------|-------------|
| Errors/Finance | 100% |
| Identity events | 100% |
| High-volume success | 10% |

### Dashboards Wired

| Dashboard | Status |
|-----------|--------|
| SLO Matrix | ✅ Via /api/kpi endpoints |
| Revenue Lineage | ✅ Via /api/kpi/revenue_by_source |
| Funnel Status | ✅ Via /api/kpi/b2b_funnel |
| Activation | ✅ Via business_events |

## Events Required (per CEO JSON)

| Event | A2 Role | Status |
|-------|---------|--------|
| identity_ok | Relay | ✅ Ready |
| page_build_requested | Relay | ✅ Ready |
| page_published | Relay | ✅ Ready |
| bandit_config | Relay | ✅ Ready |
| cta_emitted | Relay | ✅ Ready |
| cta_impression | Relay | ✅ Ready |
| checkout_completed | Relay | ✅ Ready |
| provider_registered | Relay | ✅ Ready |
| provider_listing_published | Relay | ✅ Ready |
| revenue_settled | Relay | ✅ Ready |
| credit_decrement | Relay | ✅ Ready |
| activation_first_use | Relay | ✅ Ready |

## Verdict

**A8 Wiring: ✅ COMPLIANT**

- All required schema fields available
- Header enforcement active (HTTP 428)
- Dedup and sampling rules configured
- Dashboards wired to KPI endpoints

---
**Evidence**: tests/perf/evidence/a8_post_samples.json
