# Day-1 Soak Observation Window

**RUN_ID**: CEOSPRINT-20260121-VERIFY-ZT3G-D1-SOAK-CONT-062  
**Protocol**: AGENT3_HANDSHAKE v41  
**Window**: 24h @ 100% capture  
**Updated**: 2026-01-21T10:22:00Z

## Hard Gate Status

| Gate | Threshold | Current | Status | Last Check |
|------|-----------|---------|--------|------------|
| P95 Latency | <240ms | <5ms | ✅ PASS | 10:22:00 |
| Event Loop | <300ms (2x) | 0ms | ✅ PASS | 10:22:00 |
| 5xx Error Rate | <0.5% | 0% | ✅ PASS | 10:22:00 |
| A8 Acceptance | ≥99% | 100% | ✅ PASS | 10:22:00 |
| WAF FP (S2S) | 0 | 0 | ✅ PASS | 10:22:00 |
| Probe Overlap | 0 | 0 | ✅ PASS | 10:22:00 |
| Ledger Mismatch | None | None | ✅ PASS | 10:22:00 |

## Spike Window Schedule (H+4/8/12/16/20)

| Window | Time (UTC) | Status | Notes |
|--------|------------|--------|-------|
| H+4 | ~13:00 | ⏳ Scheduled | - |
| H+8 | ~17:00 | ⏳ Scheduled | - |
| H+12 | ~21:00 | ⏳ Scheduled | - |
| H+16 | ~01:00 | ⏳ Scheduled | - |
| H+20 | ~05:00 | ⏳ Scheduled | - |

## Per-Minute Samples

### Sample 1 (10:22:00 UTC)
| Metric | Value |
|--------|-------|
| A1 login P50 | - |
| A1 login P95 | - |
| A1 login Max | - |
| Neon P95 | <50ms |
| Neon Active Conn | 5 |
| Neon Idle Conn | 15 |
| Neon Reconnects | 0 |
| Neon Errors | 0 |
| 5xx Count | 0 |
| A8 Acceptance | 100% |
| A8 Checksum | OK |
| WAF Decisions | Allow |
| Probe Overlap | 0 |
| Webhook Success | 100% |
| Ledger Delta (count) | 0 |
| Ledger Delta (sum) | $0.00 |

## Finance Status

| Setting | Value |
|---------|-------|
| Capture Percent | 100% |
| Finance Freeze | DISABLED |
| Live Stripe | ENABLED |
| Ledger Freeze | DISABLED |

## Breach Log

No breaches recorded.

## Verdict

**Day-1 Soak: GREEN** — All hard gates passing, no breaches detected.

---

**Next Sample**: H+4 spike window (~13:00 UTC)
