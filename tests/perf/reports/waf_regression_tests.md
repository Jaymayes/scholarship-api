# WAF Regression Tests

**Run ID**: CEOSPRINT-20260120-EXEC-ZT3G-GATE2-STABILIZE-033  
**Timestamp**: 2026-01-20T18:59:01Z

## Test Matrix

| Test Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Telemetry POST (normal) | 200 OK | 200 OK | ✅ PASS |
| Telemetry with _meta | 200 OK | 200 OK | ✅ PASS |
| Telemetry with S2S secret | 200 OK (bypass) | 200 OK | ✅ PASS |
| WAF block count | 0 | 0 | ✅ PASS |

## SQLi Pattern Status

| Pattern | Status |
|---------|--------|
| (\x27\|\x22\|\\x27\|\\x22) | ❌ REMOVED (caused false positives) |
| UNION/SELECT | ✅ RETAINED |
| OR 1=1 | ✅ RETAINED |
| SQL comments (--/#) | ✅ RETAINED |
| Time-based (waitfor/sleep) | ✅ RETAINED |
| Stored procedures (sp_/xp_) | ✅ RETAINED |
| File operations | ✅ RETAINED |

## Status: ✅ ALL TESTS PASSED
