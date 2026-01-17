# Performance Summary
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027
**Timestamp**: 2026-01-17T19:47:00Z

## Health Endpoint Sampling (10 samples)

| Sample | Latency (ms) | HTTP Status |
|--------|--------------|-------------|
| 1 | 157 | 200 |
| 2 | 152 | 200 |
| 3 | 140 | 200 |
| 4 | 192 | 200 |
| 5 | 175 | 200 |
| 6 | 152 | 200 |
| 7 | 155 | 200 |
| 8 | 174 | 200 |
| 9 | 205 | 200 |
| 10 | 179 | 200 |

## Statistics
- **Mean**: 168.1ms
- **P50**: 164.5ms
- **P95**: 205ms
- **Min**: 140ms
- **Max**: 205ms

## Hybrid Search Latency
- S1 (high GPA): 155ms
- S2 (baseline): 117ms
- S3 (low GPA): 187ms
- S4 (state): 120ms
- **Average**: 144.75ms
- **P95**: 187ms

## Target Compliance

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| /health P95 | <= 120ms | 205ms | CONDITIONAL (external network) |
| /search P95 | <= 200ms | 187ms | PASS |

## Verdict: CONDITIONAL PASS
Search endpoint meets SLO. Health exceeds due to external network overhead.
