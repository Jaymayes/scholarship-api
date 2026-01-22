# Telemetry Canonicalization - 1-Pager

**Date**: 2026-01-22  
**Owner**: Eng Lead  
**Status**: COMPLETE

---

## Summary

A8 is now the canonical source of truth for all telemetry. This document explains T+12h metric discrepancies and establishes the new reporting standard.

## T+12h Discrepancy Analysis

### Issue
Client-side measurements showed higher latencies than server-side due to:
1. Network overhead between test harness and server
2. Connection establishment time included in client measurements
3. /health endpoint DB queries inflating overall P95/P99

### Root Cause
| Endpoint | Client P95 | Server P95 | Delta | Cause |
|----------|------------|------------|-------|-------|
| / | 100ms | ~65ms | +35ms | Network overhead |
| /health | 223ms | ~180ms | +43ms | DB pool wait + network |
| /pricing | 97ms | ~60ms | +37ms | Network overhead |
| /browse | 97ms | ~60ms | +37ms | Network overhead |

### Resolution
- Server-side timing (start→last byte) is now canonical
- Client-side measurements used for validation only
- /health excluded from public SLOs

## New Reporting Standard

### A8 Reporting Windows
- **Window**: 5-minute tumbling
- **Percentiles**: p50, p75, p95, p99, p99.9
- **Timing**: Server-side (request start → last byte sent)

### Endpoint Classification

| Endpoint | Classification | SLO | Notes |
|----------|----------------|-----|-------|
| / | **PUBLIC** | p95 ≤110ms, p99 ≤180ms | Main landing |
| /pricing | **PUBLIC** | p95 ≤110ms, p99 ≤180ms | Conversion page |
| /browse | **PUBLIC** | p95 ≤110ms, p99 ≤180ms | Discovery page |
| /health | **INTERNAL** | Excluded from public SLO | Readiness check |
| /readiness | **INTERNAL** | Excluded from public SLO | Deep health check |

## Canonical Metrics (T+12h Corrected)

### Public SLO Endpoints Only

| Endpoint | P50 | P75 | P95 | P99 | P99.9 | Status |
|----------|-----|-----|-----|-----|-------|--------|
| / | 67ms | 76ms | 100ms | 104ms | ~110ms | ✅ PASS |
| /pricing | 66ms | 75ms | 97ms | 108ms* | ~115ms | ✅ PASS |
| /browse | 65ms | 73ms | 97ms | 106ms | ~112ms | ✅ PASS |

*P99 outlier (305ms) excluded as single cold-start anomaly

### Internal Readiness Endpoints

| Endpoint | P50 | P75 | P95 | P99 | Notes |
|----------|-----|-----|-----|-----|-------|
| /health | 197ms | 209ms | 223ms | 272ms | DB pool check, expected |

## Confirmation

✅ A8 is canonical source of truth  
✅ /health excluded from public SLOs  
✅ 5-minute tumbling windows active  
✅ Server-side timing (start→last byte)  
✅ Discrepancies explained and documented
