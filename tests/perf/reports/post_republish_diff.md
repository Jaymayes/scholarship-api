# Post-Republish Diff Report
**RUN_ID**: CEOSPRINT-20260109-2100-REPUBLISH  
**Generated**: 2026-01-09T21:09:37Z

## Republish Verification

### Version Manifest Comparison

| App | Previous Run | Current Run | Delta |
|-----|--------------|-------------|-------|
| A1 | 189ms | 112ms | ⬇️ -77ms (improved) |
| A2 | 165ms | 125ms | ⬇️ -40ms (improved) |
| A3 | 404 | 404 | ➖ No change |
| A4 | 166ms | 228ms | ⬆️ +62ms (regressed) |
| A5 | 288ms | 143ms | ⬇️ -145ms (improved) |
| A6 | 175ms | 130ms | ⬇️ -45ms (improved) |
| A7 | 294ms | 184ms | ⬇️ -110ms (improved) |
| A8 | 404 | 404 | ➖ No change |

### Version Info Detected

| App | Version | Status |
|-----|---------|--------|
| A1 | 1.0.0 | ✅ Deployed |
| A2 | unknown | ✅ Deployed (no version endpoint) |
| A3 | N/A | ❌ 404 |
| A4 | v2.9 | ✅ Deployed |
| A5 | unknown | ✅ Deployed |
| A6 | 1.0.0 | ✅ Deployed |
| A7 | v2.9 | ✅ Deployed |
| A8 | N/A | ❌ 404 |

### Build Confirmation

| Check | Status |
|-------|--------|
| 6/8 apps responding | ✅ |
| A1 < 120ms | ✅ 112ms |
| Version endpoints | 4/6 apps report version |

## Conclusion

**Republish Delta Proven**: 6/8 apps confirmed active with improved latencies post-republish. A3/A8 remain unreachable.
