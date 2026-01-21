# Day-1 Soak Plan

**RUN_ID**: CEOSPRINT-20260121-VERIFY-ZT3G-D1-SOAK-057  
**Protocol**: AGENT3_HANDSHAKE v39 (Day-1 Soak + V2 Sprint-1)  
**Duration**: 24 hours at 100% traffic

## Monitoring Schedule

### Continuous Sampling (Every 60 seconds)
- System health check
- P50/P95/Max latency
- Error rate (5xx threshold: <0.5%)
- A8 acceptance rate (threshold: ≥99%)
- WAF decisions and false positives
- Probe overlap detection
- Live vs shadow reconciliation counters

### Spike Windows (Scheduled)
| Hour | Type | Description |
|------|------|-------------|
| +1h | Provider Login Burst | 20 concurrent provider logins |
| +4h | SEO POST Burst | 50 concurrent page submissions |
| +8h | Provider Login Burst | 30 concurrent provider logins |
| +12h | SEO POST Burst | 75 concurrent page submissions |
| +16h | Provider Login Burst | 40 concurrent provider logins |
| +20h | SEO POST Burst | 100 concurrent page submissions |

## Hard Gates (Breach → Immediate Rollback)

### Financial Correctness
- Live vs shadow ledger mismatch
- Orphan entries in either ledger
- Missing webhook for completed charge/refund
- Refund failure or timeout
- Any mutation without idempotency key

### Reliability
- 5xx error rate ≥0.5% in any minute
- A8 acceptance <99% sustained
- A8 POST→GET checksum mismatch

### Performance
- A1 login P95 >240ms on 2 consecutive samples
- A1 login any sample >320ms
- Neon DB P95 >150ms
- Neon connection error
- Event loop ≥300ms on 2 consecutive samples

### Security
- WAF false positive on allowed S2S telemetry
- Probe overlap detected
- Trusted health probes receive 429/4xx

## Rollback Procedure

If any hard gate breached:
```
CAPTURE_PERCENT=0
LEDGER_FREEZE=true
PROVIDER_INVOICING_PAUSED=true
FEE_POSTINGS_PAUSED=true
LIVE_STRIPE_CHARGES=BLOCKED
```

## Success Criteria

After 24 hours with no hard gate breaches:
- All samples within thresholds
- Finance reconciliation balanced
- A8 telemetry complete
- Zero security incidents

**Status**: ✅ PLAN ACTIVE
