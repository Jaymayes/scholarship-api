# Gate A Execution Checklist - auto_com_center

**Window**: 20:00-20:15 UTC  
**Evidence Due**: 20:30 UTC  
**CEO Review**: 20:45 UTC  
**DRI**: Agent3

## Pre-Gate Preparation (Before 19:45 UTC)

- [ ] Verify Postmark domain status: VERIFIED
- [ ] Confirm SPF record: PASS
- [ ] Confirm DKIM signature: PASS
- [ ] Confirm DMARC policy: p=none (approved for Gate A)
- [ ] Verify webhook endpoint: LIVE and responding
- [ ] Seed list prepared: 20 addresses (Gmail, Outlook, iCloud mix)
- [ ] 30K webhook replay dataset ready
- [ ] Monitoring dashboards active
- [ ] request_id tracing enabled
- [ ] Evidence collection scripts ready

## Critical Window (19:45-20:30 UTC)

**NO CONTEXT SWITCHING - Gate A focus only**

## Gate A Execution (20:00-20:15 UTC)

### Test Sequence

#### 1. Inbox Placement Test (20:00-20:05 UTC)
- [ ] Send to 20-address seed list
- [ ] Verify SPF/DKIM/DMARC alignment in headers
- [ ] Check inbox placement (target: 100%, threshold: ≥95%)
- [ ] Capture email headers with auth results
- [ ] Screenshot inbox delivery for each provider

#### 2. Performance Test (20:05-20:10 UTC)
- [ ] Execute 500 test sends
- [ ] Measure send API latency (target: <100ms, threshold: ≤120ms)
- [ ] Capture P95, P99, max latency
- [ ] Monitor error rate (threshold: ≤0.10%)
- [ ] Generate latency histograms

#### 3. Webhook Reliability Test (20:10-20:15 UTC)
- [ ] Replay 30,000 event webhooks from staging
- [ ] Verify zero data loss
- [ ] Verify no message reordering beyond tolerance
- [ ] Verify idempotency keys working
- [ ] Confirm request_id lineage in all logs
- [ ] Check BI sink for complete event stream

## Pass Thresholds (All Must Pass)

### Hard Gates
- [ ] Inbox placement ≥95% primary inbox
- [ ] P95 latency ≤120ms (target <100ms)
- [ ] Error rate ≤0.10%
- [ ] SPF: PASS on all domains
- [ ] DKIM: PASS on all domains
- [ ] DMARC: PASS (p=none acceptable)
- [ ] Webhooks: 30K replay clean
- [ ] Zero data loss detected
- [ ] Zero message reordering
- [ ] Idempotency verified
- [ ] request_id lineage intact

## Evidence Collection (20:15-20:30 UTC)

### Required Artifacts
- [ ] Email headers with SPF/DKIM/DMARC results
- [ ] Inbox placement screenshots (Gmail, Outlook, iCloud)
- [ ] Seed list delivery matrix
- [ ] P95 latency histogram
- [ ] P99 latency metrics
- [ ] Error rate telemetry
- [ ] 500-send performance data
- [ ] Webhook replay logs (30K events)
- [ ] request_id trace samples
- [ ] Prometheus/ELK dashboard screenshots
- [ ] SHA-256 manifest of all evidence

### Evidence Bundle Structure
```
evidence/20251112/gate_a/
├── headers/
│   ├── gmail_headers.txt
│   ├── outlook_headers.txt
│   └── icloud_headers.txt
├── screenshots/
│   ├── gmail_inbox.png
│   ├── outlook_inbox.png
│   └── icloud_inbox.png
├── performance/
│   ├── latency_histogram.png
│   ├── p95_p99_metrics.json
│   └── error_rate.json
├── webhooks/
│   ├── replay_30k_results.log
│   ├── idempotency_verification.log
│   └── request_id_traces.log
├── monitoring/
│   ├── prometheus_screenshot.png
│   └── elk_screenshot.png
└── manifest.json (with SHA-256 checksums)
```

## Rollback Triggers (If Any Fail)

### Immediate Rollback If:
- Inbox placement <90% for 2 consecutive seed runs
- P95 >140ms for 5 minutes
- 5xx error rate ≥0.5% for 2 minutes
- Webhook data loss detected

### Rollback Actions:
1. Route traffic to secondary pool with reduced throttles
2. Extend warm-up by 7-14 days
3. Hold all outbound sends from scholarship_agent
4. Open sev-2 incident for remediation
5. Re-run Gate A within 24 hours

## CEO Report (20:45 UTC)

### Status Indicators
- **GREEN**: All thresholds passed, ready for GO at 20:30 UTC
- **YELLOW**: 1-2 minor issues, conditional GO with monitoring
- **RED**: Hard gate failed, rollback and remediate

### Report Template
```
APPLICATION NAME: auto_com_center
APP_BASE_URL: https://auto-com-center-jamarrlmayes.replit.app
Gate A Status: GREEN / YELLOW / RED
Execution Time: 20:00-20:15 UTC
Evidence Published: 20:30 UTC

PASS Criteria Results:
- Inbox placement: [%] (≥95% required) - PASS / FAIL
- P95 latency: [ms] (≤120ms required) - PASS / FAIL
- Error rate: [%] (<0.10% required) - PASS / FAIL
- SPF/DKIM/DMARC: PASS / FAIL
- Webhooks 30K replay: PASS / FAIL
- Data loss: NONE / DETECTED
- request_id lineage: INTACT / BROKEN

Evidence SHA-256: [hash]

Recommendation: GO / CONDITIONAL GO / NO-GO
Rationale: [brief explanation]

Next Steps: [if applicable]
```

## Post-Gate Actions (If GREEN)

- [ ] Conditional GO issued at 20:30 UTC
- [ ] DMARC monitoring begins (hold p=none for 24-48h)
- [ ] Deliverability telemetry streaming
- [ ] Prepare for scholarship_agent warm-up (pending Legal + Gate C)
- [ ] Monitor inbox placement ≥95% sustained
- [ ] Monitor complaint rate target <0.1%
