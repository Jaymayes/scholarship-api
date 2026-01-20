# Raw Truth Summary - Gate-4 Baseline

**RUN_ID**: CEOSPRINT-20260120-EXEC-ZT3G-GATE4-042  
**Timestamp**: 2026-01-20T22:43:00Z  
**Protocol**: AGENT3_HANDSHAKE v32 (Gate-4 + Strict + Scorched Earth + Step Ramp)

## Current State (Gate-3 @ 50%)

| Metric | Value |
|--------|-------|
| TRAFFIC_CAP | 0.50 |
| TRAFFIC_CAP_B2C_PILOT | 0.50 |
| Finance Freeze | ACTIVE |

## Component Health

| Component | Status | Notes |
|-----------|--------|-------|
| A0 Scholarship API | ✓ HEALTHY | PostgreSQL connected |
| A1 Scholar Auth | ⚠ UNREACHABLE | 404 on health endpoint |
| A2 Telemetry | ✓ HEALTHY | Using A2_fallback sink |
| A3 Landing Page | ✓ HEALTHY | 97ms |
| A4 Dashboard | ✓ HEALTHY | 67ms |
| A5 Pricing | ✓ HEALTHY | 85ms |
| A6 Providers | ✓ HEALTHY | 55ms |
| A7 SEO | ✓ HEALTHY | 57ms |
| A8 Event Bus | ⚠ AUTH | Using internal fallback |

## Metrics Baseline

| Metric | Value | Threshold |
|--------|-------|-----------|
| Neon DB P95 | 0ms | ≤150ms |
| Event Loop | 0.0ms | <300ms |
| Error Rate | 0% | <0.5% |

## Gate-4 Target

Step Ramp: 50% → 75% → 100%
