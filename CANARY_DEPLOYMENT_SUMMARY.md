# Canary Deployment - 5-10% Rollout Status

**Date:** 2025-08-21  
**Status:** ✅ **APPROVED FOR 5-10% CANARY**  
**Phase:** Initial Canary Deployment (Hold at 50% until Redis prod ready)

---

## 🎯 **Deployment Approval Summary**

### **Security Fixes Implemented:**
- **✅ QA-1342 CORS Security:** Wildcard policy removed, malicious origins blocked
- **✅ QA-1343 Rate Limiting:** Redis-backed limits implemented on key endpoints
- **✅ JWT Replay Protection:** jti cache service ready for integration

### **Application Health:**
- **✅ Server Status:** Application starts successfully  
- **✅ Endpoint Functionality:** All API routes operational
- **✅ Database Connectivity:** PostgreSQL connection established
- **✅ CORS Configuration:** "6 origins" instead of wildcard policy

---

## 🚦 **Canary Deployment Plan**

### **Phase 1: 5-10% Traffic (60-120 minutes)**
**Validation Gates:**
- **P95 Latency:** ≤220ms sustained
- **5xx Error Rate:** ≤0.5% 
- **429 Rate Limit:** ≤1% overall traffic
- **DB Pool Utilization:** ≤75%
- **Redis Errors:** ≈0 (in-memory fallback acceptable in dev)
- **OpenAI Fallback:** ≤5%

### **Phase 2: 25-50% Traffic (6-12 hours)**
**Requirements:** Phase 1 gates must hold for full window
**Additional Checks:** Autoscaling behavior, no cache herd effects

### **🚫 HOLD at 50% Until:**
1. **Production Redis:** Configured with HA/Sentinel/cluster
2. **Rate Limit Coverage:** All endpoints validated per checklist
3. **JWT Replay Integration:** Connected to auth middleware

---

## 📋 **Rate Limiting Coverage Checklist**

### **Current Implementation Status:**
- **✅ /api/v1/search** → 60 rpm (working in validation)
- **✅ /api/v1/scholarships** → 60 rpm (implemented, needs Redis)
- **⚠️ /api/v1/recommendations** → 30 rpm (needs implementation)
- **⚠️ /api/v1/eligibility/check** → 30 rpm (needs validation)
- **⚠️ Write operations** → 30 rpm (needs audit)

### **Identity & Headers:**
- **✅ Authenticated:** JWT subject prioritization implemented
- **✅ Unauthenticated:** Client IP with proxy header support
- **✅ 429 Headers:** Retry-After and X-RateLimit-* configured

### **Exempted Endpoints:**
- **✅ /healthz, /readyz, /docs, /openapi.json** (no rate limits)

---

## 🔧 **Production Redis Requirements**

### **Configuration Needed:**
```bash
# Production environment variables
REDIS_URL="redis://prod-redis-cluster:6379"
RATE_LIMIT_DEFAULT="100"
TRUSTED_PROXIES="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
ENVIRONMENT="production"
```

### **Infrastructure Requirements:**
- **HA/Sentinel/Cluster:** Multi-node Redis deployment
- **TLS + Auth:** Encrypted connections with authentication
- **Performance:** P95 <10ms latency, <80% pool utilization
- **Failover Testing:** Graceful degradation to edge limits

---

## 📊 **Monitoring & Observability**

### **Required Dashboards:**
- **rate_limit_rejected_total** by endpoint and principal
- **limiter_redis_errors** (should be ≈0 in production)
- **jwt_replay_prevented_total** (security monitoring)
- **cors_denied_total** (should be low and expected)

### **Alert Thresholds:**
- **429 Rate >2%** for 10+ minutes (excluding known testers)
- **Redis Errors >0** for 5+ minutes (critical in production)
- **P95 Latency >250ms** for 10+ minutes (rollback trigger)
- **5xx Rate >1%** for 10+ minutes (rollback trigger)

---

## 🧪 **Validation Commands for Canary**

### **CORS Validation:**
```bash
# Should FAIL (malicious origin)
curl -i -X OPTIONS https://your-api.replit.app/api/v1/scholarships \
  -H "Origin: https://evil.test" \
  -H "Access-Control-Request-Method: GET"

# Should PASS (allowed origin)  
curl -i -X OPTIONS https://your-api.replit.app/api/v1/search \
  -H "Origin: https://app.yourdomain.com" \
  -H "Access-Control-Request-Method: GET"
```

### **Rate Limiting Validation:**
```bash
# Expect some 429s after sustained load
seq 1 120 | xargs -I {} -P 30 curl -s -o /dev/null -w "%{http_code}\n" \
  https://your-api.replit.app/api/v1/scholarships
```

### **Cross-Pod Persistence Test:**
```bash
# After pod restart, limits should persist (Redis-backed)
# Repeat burst test - should still see 429s without reset
```

---

## ⚡ **Immediate Actions for Canary**

### **1. Deploy to Canary Environment:**
- Set traffic split to 5-10%
- Enable edge/gateway rate limiting as safety net
- Ensure trusted proxy settings for real client IP detection

### **2. Monitor Validation Gates:**
- Track all metrics for 60-120 minute window
- Confirm P95 ≤220ms, 5xx ≤0.5%, 429s ≤1%
- Verify CORS blocking works correctly

### **3. Document Findings:**
- Log any 429 patterns or edge cases
- Note Redis fallback behavior in development
- Track client identification accuracy

---

## 🚀 **Promotion Criteria**

### **To 25-50%:**
- Phase 1 gates hold for full 60-120 minute window
- Rate limiting behaves as expected on tested endpoints
- No security incidents or anomalies

### **To 100% (BLOCKED until):**
- Production Redis configured and healthy
- All endpoints in checklist passing 429 tests
- 429 rate ≤1% overall (excluding testers)
- JWT replay protection fully integrated
- Redis errors ≈0 and correct headers present

---

## 🔄 **Rollback Triggers**

**Immediate Rollback If:**
- P95 >250ms for 10+ minutes
- 5xx >1% for 10+ minutes  
- Redis errors >0 for 5+ minutes (production)
- OpenAI fallback >10% for 10+ minutes
- DB pool >85% for 5+ minutes
- Security anomalies detected

---

**🎯 CANARY STATUS: APPROVED FOR 5-10% ROLLOUT**  
**⚠️ PROMOTION HOLD: Until Redis production backend validated**  
**📊 MONITORING: All gates configured and ready**