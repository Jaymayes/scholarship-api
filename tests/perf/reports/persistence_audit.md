# Persistence Audit Report
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3G-RERUN-006
**Mode**: READ-ONLY (no fixes applied)
**Generated**: 2026-01-12T04:13:24Z

## Persistence Status: **REGRESSION DETECTED** ❌

### Port 5000
- **Status**: CLEAN ✅
- **Observation**: No listeners on port 5000
- **Persistence**: VERIFIED

### A3 Binding
- **Status**: HTTP 404 ❌
- **Observation**: Returns 404 at 82ms (edge response, app not running)
- **Persistence**: NOT VERIFIED (was never fixed in prior run)

### A8 Binding
- **Status**: HTTP 404 ❌
- **Observation**: Returns 404 at 78ms (edge response, app not running)
- **Persistence**: NOT VERIFIED (was never fixed in prior run)

### A6 No-Touch
- **Status**: HTTP 200 ✅
- **Latency**: 120ms (at SLO)
- **Persistence**: VERIFIED

## Conclusion
A3 and A8 remain in failed state (HTTP 404). The "Gold Standard" claim from Run 005 was incorrect—those apps were never accessible from this workspace and remain unfixed.
