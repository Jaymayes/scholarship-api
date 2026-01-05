# Conflicts Resolution Table
**Audit Date**: 2026-01-05T19:30:00Z

| # | Prior Claim | Fresh Measurement | Explanation |
|---|-------------|-------------------|-------------|
| 1 | A2 /ready returns 404 | **200 OK** (P95=131ms, n=50) | Transient during deployment; endpoint exists and passes SLO |
| 2 | A7 P95 ~216-559ms | **P95=234ms** (n=50, 95% CI ±12ms) | Confirmed exceeds 150ms target; synchronous SendGrid calls likely cause |
| 3 | A8 Revenue Blocked | **8/8 apps healthy** | Operational mode, not fault; A3 orchestration not running = no live payments |
| 4 | A8 $0 Revenue | **Correct behavior** | No live Stripe transactions; test data properly filtered; Demo Mode needed for visibility |
| 5 | AUTH_FAILURE from scholar_auth | **0% error rate** (n=10) | False positive; A1 healthy, OIDC chain verified, 1 RSA key published |
| 6 | Database unreachable | **All DBs responding** | A1/A2 ready endpoints return 200 with DB checks passing |

## Evidence Summary

### A2 /ready (Conflict #1)
```
HTTP/1.1 200 OK
{"status":"ready","services":{"api":"ready","database":"ready","stripe":"configured"}}
P95: 131.19ms (under 150ms target)
```

### A7 Latency (Conflict #2)
```
P50: 169.65ms
P95: 234.46ms (exceeds 150ms by 84.5ms)
P99: 304.04ms
Mean: 177.56ms ± 12.45ms (95% CI)
```

### A1 AUTH (Conflict #5)
```
/health: 200 OK
/ready: 200 OK
OIDC Discovery: 200 OK
JWKS Keys: 1 (scholar-auth-prod-20251016-941d2235, RSA)
Error rate: 0/10 (0%)
```

## Verdict

- **Issue A**: ✅ FALSE POSITIVE - A2 /ready works
- **Issue B**: ⚠️ CONFIRMED - A7 P95 exceeds SLO
- **Issue C**: ⚠️ CONFIRMED - A8 banners need TTL
- **Issue D**: ⚠️ EXPLAINED - $0 is correct (no live payments)
- **AUTH_FAILURE**: ✅ FALSE POSITIVE - A1 fully operational
